"""Explicit five-business-cell region contract. Legacy TR proofs are untouched.
No UI/capture here: derive selectors and validate public semantic/region evidence.
"""
import json,re,math
import governance_projection as gp
from visible_capture import require as need, SAFETY
CONTRACT='notice-five-business-cells-v1'
MANUAL='notice-five-business-cells-v2'
LOCAL='manual-local-business-preview-v2'
FIELDS=['reason','subject','object','effective_status','disposal']
HEADERS=gp.HEADERS[:5]
def command_namespace(manual,projection_contract=None):
 gp.projection_schema(projection_contract,manual)
 return (MANUAL if manual else CONTRACT)+(':'+gp.RECTIFICATION_MARKER if projection_contract else '')
def command_projection(command):
 keys=[e.get('key','') for e in command.get('elements',[])];marked=[(':rectification-' in k) for k in keys]
 if any(marked):
  need(bool(keys) and all(k.startswith(command_namespace(k.startswith(MANUAL+':'),gp.RECTIFICATION_CONTRACT)+':') for k in keys),'business-projection-namespace-invalid')
  return gp.RECTIFICATION_CONTRACT
 return None

def is_command(command):return any(e.get('key','').startswith('notice-five-business-cells-') for e in command.get('elements',[]))
def spec(tree,groupid,*,actual_url=None,projection_contract=None):
 p=gp.project(tree,groupid,actual_url=actual_url,projection_contract=projection_contract);ns=list(gp.walk(tree['root']));heads=[];rows=[]
 for field in HEADERS:
  th=gp.one([n for n in ns if n.get('tag')=='th' and n.get('role')=='columnheader' and n.get('name')==field],'business-header')
  label=gp.one([n for n in gp.walk(th) if 'governance_merchant-Table-HeadCellContentTitle' in gp.cls(n)],'business-header-label');need(not label.get('children') and label.get('name')==field,'business-header-label-not-exact-leaf');heads.append({'field':field,'th_selector':th['selector'],'selector':label['selector'],'text':field,'text_selectors':[label['selector']]})
 for selector,rowtext in p['rows'].items():
  tr=gp.one([n for n in ns if n.get('selector')==selector],'business-row');cells=tr['children'];rows.append({'notice_id':rowtext[0],'tr_selector':selector,'cells':[{'index':i,'field':FIELDS[i],'selector':n['selector'],'text':n.get('name',''),'text_selectors':[x['selector'] for x in gp.walk(n) if x.get('name') and x.get('tag') not in ('img','svg','input','textarea','select')]} for i,n in enumerate(cells[:5])]})
 badges={}
 for row in rows:
  for cell in row['cells']:
   node=gp.one([n for n in ns if n.get('selector')==cell['selector']],'business-cell-source');found=[]
   for n in gp.walk(node):
    children=n.get('children',[])
    if n.get('tag')=='sup' and len(gp.cls(n))==3 and set(gp.cls(n))=={'governance_merchant-badge-sup','governance_merchant-badge-sup-placement-top-right','governance_merchant-badge-sup-show'} and not n.get('name') and len(children)==1:
     child=children[0]
     if child.get('tag')=='div' and len(gp.cls(child))==3 and set(gp.cls(child))=={'governance_merchant-badge-dot','governance_merchant-badge-dot-placement-top-right','governance_merchant-badge-type-danger'} and not child.get('name') and not child.get('children') and all(x.get('attributes',{}).get('role') is None and x.get('attributes',{}).get('tabindex') is None for x in (n,child)):found.append({'selector':n['selector'],'class':n['attributes']['class'],'child_selector':child['selector'],'child_class':child['attributes']['class']})
   badges[cell['selector']]=found
 ancestry={}
 def parents(n,path):
  if n.get('selector'):ancestry[n['selector']]=list(path)
  for child in n.get('children',[]):parents(child,[*path,n.get('selector')])
 parents(tree['root'],[])
 return {**({'projection_contract':projection_contract} if projection_contract else {}),**({'manual_source_ancestors':{c['selector']:ancestry[c['selector']] for row in rows for c in row['cells']}} if actual_url is not None else {}),'contract':CONTRACT,'date_selector':gp.one([n for n in ns if n.get('tag')=='input' and n.get('name')=='违规时间'],'business-date')['selector'],'headers':heads,'rows':rows,'identity_badges':badges,'partial_source':{'text_leaf_ancestors':ancestry,'text_leaf_nodes':{n['selector']:{k:n.get(k)for k in ('tag','attributes')}for n in ns if n.get('selector')},'structural_ancestors':{n['selector']:{'tag':n['tag'],'rows':[x['selector'] for x in gp.walk(n) if x.get('tag')=='tr']} for n in ns if n.get('selector')=='#main-app > section > section'},'containers':[n['selector'] for n in ns if n.get('attributes',{}).get('class')=='governance_merchant-Table-Container governance_merchant-Table-Container_scrollable'],'nodes':{c['selector']:[{k:n.get(k) for k in ('selector','tag','name','attributes','children')} for n in gp.walk(gp.one([n for n in ns if n.get('selector')==c['selector']],'partial-cell'))] for row in rows for c in row['cells']}}}
def validate_base(p,inputs):
 c=inputs['command'];s=inputs['business_spec'];manual=inputs.get('screenshot_identity') is not None;need(s['contract']==CONTRACT and all(e['key'].startswith(command_namespace(manual,s.get('projection_contract'))+':') for e in c['elements']),'business-command-contract-invalid')
 need(command_projection(c)==s.get('projection_contract'),'business-projection-contract-mismatch')
 need(p.get('diagnostic_build') in ('viewport-notice-business-cells-v3','viewport-notice-business-cells-v4','viewport-notice-business-cells-v5','viewport-notice-business-cells-v6','viewport-notice-business-cells-v7','viewport-notice-business-cells-v8','viewport-notice-business-cells-v9-provider-manual-preview-v2','viewport-notice-business-cells-v10-business-text-diagnostic-v1','viewport-notice-business-cells-v11-manual-own-text-overflow-v2','viewport-notice-business-cells-v12-rectification-projection-v3','viewport-notice-business-cells-v13-fractional-auto-padding-v1') and p.get('evidence_contract')==CONTRACT and p.get('source')=='local-dom-bridge' and p.get('method')=='public-DOM-semantic-viewport-proof' and p.get('safety_version')==SAFETY and p.get('hash_contract')==gp.projection_schema(s.get('projection_contract'),manual) and p.get('hash_scope')=='versioned-public-DOM-projection','business-base-contract-invalid')
 need(p.get('scope')=={k:c[k] for k in ('tabId','windowId','groupid')} and p.get('url')==inputs['url'] and p.get('source_sha256')==c['source_sha256'] and p.get('dom_sha256')==c['dom_sha256'] and type(p.get('epoch')) is int and p['epoch']>=0 and p.get('viewport_only') is True and p.get('pixel_actions_used') is False,'business-base-scope-invalid')
 actual=p.get('elements',[]);need(len(actual)==len(c['elements']),'business-original-elements-incomplete')
 flags=('rendered','viewport_contained','text_unclipped','unsupported_css_absent','possible_overlay_absent')
 for a,e in zip(actual,c['elements']):
  need(all(a.get(k)==e[k] for k in ('key','kind','notice_id','locator')) and a.get('text')==e['expected_text'],'business-original-element-changed');need(all(type(a.get(k)) is bool for k in (*flags,'fully_visible')) and a['fully_visible']==all(a[k] for k in flags),'business-original-flags-inconsistent')
 need(type(p.get('all_fully_visible')) is bool and p['all_fully_visible']==all(a['fully_visible'] for a in actual),'business-original-all-flags-inconsistent')
 need(type(p.get('pixel_coordinates_returned')) is bool and p['pixel_coordinates_returned']==(p['diagnostic_build']=='viewport-notice-business-cells-v13-fractional-auto-padding-v1'or any(a.get('containment_diagnostic',{}).get('reason_count',0)>0 for a in actual)),'business-original-coordinate-disclosure-invalid')
 headers=p.get('business_headers',[]);rows=p.get('business_cells',[]);need(len(headers)==5 and len(rows)==len(s['rows']),'business-five-groups-incomplete')
 for a,e in zip(headers,s['headers']):
  need(all(a.get(k)==v for k,v in e.items()),'business-header-structure-changed');validate_geometry(a['geometry'],allow_ellipsis=False,selectors=e['text_selectors'])
 for a,e in zip(rows,s['rows']):
  need(a.get('notice_id')==e['notice_id'] and a.get('tr_selector')==e['tr_selector'] and len(a.get('cells',[]))==5,'business-notice-five-direct-cells-required')
  for cell,want in zip(a['cells'],e['cells']):
   need(all(cell.get(k)==v for k,v in want.items()),'business-cell-field-order-or-source-changed')
   if p['diagnostic_build']=='viewport-notice-business-cells-v13-fractional-auto-padding-v1':validate_text_leaf_evidence(cell['geometry'],want,s['partial_source']['nodes'][want['selector']],s['partial_source']['text_leaf_ancestors'],s['partial_source']['text_leaf_nodes'],cell.get('box'),p.get('business_viewport'))
   else:need('text_leaf_evidence'not in cell['geometry'],'business-historical-leaf-schema-forbidden')
   validate_geometry(cell['geometry'],allow_ellipsis=True,selectors=want['text_selectors'],identity_badges=s.get('identity_badges',{}).get(want['selector'],[]),manual=manual)
 date=p.get('business_date',{});need(date.get('selector')==s['date_selector'] and date.get('text')==next(e['expected_text'] for e in c['elements'] if e['kind']=='date-filter'),'business-date-changed');validate_geometry(date['geometry'],allow_ellipsis=False,selectors=[s['date_selector']])
 if manual:
  import screenshot_identity as identity
  a=inputs['screenshot_identity'];pub=p.get('public_identity',{});need(p.get('preview_contract')==MANUAL and pub.get('provider')==a['identity']['provider'] and pub.get('actual_url')==inputs['url'],'business-public-identity-changed')
  card=pub.get('visible_card')
  if card is not None:
   with identity.api() as (d,producer):d.nav.identity({'truncated':False,'root':card},a['identity'])
  previews=validate_manual_previews(p,s)
  validate_own_text_overflows(p,s,previews)
 else:validate_partial_previews(p,s)
 return p

def text_leaf_clip_box(a,source_context):
 import math
 c=a['clip_source'];need(isinstance(c,dict) and set(c)=={'rect','metrics','style','scrollbar_pseudo','table_container'},'business-leaf-clip-source-schema');r=c['rect'];m=c['metrics'];s=c['style'];need(isinstance(r,dict) and set(r)=={'left','top','right','bottom','width','height'}and all(type(v)in(int,float)and math.isfinite(v)for v in r.values())and r['width']>=0 and r['height']>=0 and r['right']-r['left']==r['width']and r['bottom']-r['top']==r['height'],'business-leaf-clip-source-rect')
 metric_keys={'clientLeft','clientTop','clientWidth','clientHeight','offsetWidth','offsetHeight','scrollWidth','scrollHeight'};style_keys={'display','position','boxSizing','paddingLeft','paddingRight','paddingTop','paddingBottom','borderLeftWidth','borderTopWidth','borderRightWidth','borderBottomWidth','overflowX','overflowY','scrollbarGutter','scrollbarWidth','transform','zoom','clip','clipPath','maskImage','webkitMaskImage','filter','opacity','textOverflow','webkitLineClamp'}
 need(isinstance(m,dict) and set(m)==metric_keys and all(type(v)in(int,float)and math.isfinite(v)and v>=0 for v in m.values())and isinstance(s,dict) and set(s)==style_keys and all(isinstance(v,str)and len(v)<=200 for v in s.values()),'business-leaf-clip-source-metrics')
 node=source_context.get(a['selector']);known_table=node is not None and node.get('tag')=='div'and node.get('attributes',{}).get('class')=='governance_merchant-Table-Container governance_merchant-Table-Container_scrollable';need(type(c['table_container'])is bool and c['table_container']==known_table,'business-leaf-clip-table-source')
 need(a['x']==(s['overflowX']in('hidden','clip','auto','scroll'))and a['y']==(s['overflowY']in('hidden','clip','auto','scroll')),'business-leaf-clip-axis-derived')
 unsupported=any(s[k]and s[k]!=v for k,v in [('transform','none'),('clip','auto'),('clipPath','none'),('maskImage','none'),('webkitMaskImage','none'),('filter','none')])or s['zoom']not in('1','normal')or s['opacity']not in('1','1.0')
 need(not unsupported,'business-leaf-clip-effect')
 result={'left':r['left']+m['clientLeft'],'top':r['top']+m['clientTop'],'right':r['left']+m['clientLeft']+m['clientWidth'],'bottom':r['top']+m['clientTop']+m['clientHeight']}
 ps=c['scrollbar_pseudo'];default_pseudo=ps=={'::-webkit-scrollbar':{'display':'inline','width':'auto','height':'auto'},'::-webkit-scrollbar:horizontal':{'display':'','width':'','height':''},'::-webkit-scrollbar:vertical':{'display':'','width':'','height':''}}
 if not known_table:need(ps is None,'business-leaf-nontable-pseudo')
 if known_table and s['overflowX']==s['overflowY']=='auto'and s['scrollbarGutter']==s['scrollbarWidth']=='auto'and s['display']=='block'and s['position']=='relative'and s['boxSizing']=='border-box'and all(s[k]=='0px'for k in('paddingLeft','paddingRight','paddingTop','paddingBottom','borderLeftWidth','borderRightWidth','borderTopWidth','borderBottomWidth'))and m['clientLeft']==m['clientTop']==0 and all(type(m[k])is int and m[k]>0 for k in('clientWidth','clientHeight','offsetWidth','offsetHeight','scrollWidth','scrollHeight'))and m['offsetWidth']==m['clientWidth']==math.floor(r['width']+.5)and m['offsetHeight']==m['clientHeight']==math.floor(r['height']+.5)and default_pseudo:return {k:r[k]for k in('left','top','right','bottom')}
 if s['overflowX']==s['overflowY']=='hidden'and s['scrollbarGutter']=='auto'and s['display']in('block','flow-root','inline-block','flex','inline-flex','grid','inline-grid','table-cell'):
  ks=['borderLeftWidth','borderTopWidth','borderRightWidth','borderBottomWidth'];vs=[float(s[k][:-2])if re.fullmatch(r'(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)px',s[k])else None for k in ks]
  if all(v is not None for v in vs)and vs[0]+vs[2]<=r['width']and vs[1]+vs[3]<=r['height']:return {'left':r['left']+vs[0],'top':r['top']+vs[1],'right':r['right']-vs[2],'bottom':r['bottom']-vs[3]}
 return result

def validate_text_leaf_evidence(g,want,source_nodes,source_ancestors,source_context,expected_cell,expected_viewport):
 leaf=g.get('text_leaf_evidence');need(isinstance(leaf,dict) and set(leaf)=={'schema','limits','cell','viewport','owners','leaves','full','excerpt_eligible','unavailable'} and leaf['schema']=='source-bound-public-text-grapheme-clips-v1' and leaf['limits']=={'nodes':64,'parts':64,'text_units':16000,'graphemes':512,'rectangles':2048,'ancestors':40},'business-text-leaf-schema')
 need(type(leaf['full'])is bool and type(leaf['excerpt_eligible'])is bool,'business-text-leaf-flags')
 if leaf['unavailable'] is not None:
  need(isinstance(leaf['unavailable'],str) and leaf['unavailable'].startswith('leaf-') and len(leaf['unavailable'])<=100 and leaf['full']is False and leaf['excerpt_eligible']is False and leaf['owners']==leaf['leaves']==[] and leaf['cell']is None and leaf['viewport']is None,'business-text-leaf-unavailable');return False,False
 import math
 def box(v,positive=False):
  need(isinstance(v,dict) and set(v)=={'left','top','right','bottom','width','height'} and all(type(x)in(int,float)and math.isfinite(x)for x in v.values())and v['right']-v['left']==v['width'] and v['bottom']-v['top']==v['height'] and v['width']>0 and v['height']>0,'business-text-leaf-box');return v
 cell=box(leaf['cell']);viewport=box(leaf['viewport']);need(cell==expected_cell and viewport==expected_viewport,'business-text-leaf-same-proof-cell-viewport');need(isinstance(source_nodes,list)and 1<=len(source_nodes)<=64,'business-text-leaf-source-bounds');source={n['selector']:n for n in source_nodes};need(len(source)==len(source_nodes)and want['selector']in source,'business-text-leaf-source-unique')
 total_parts=0;total_text=0
 owners=leaf['owners'];need(isinstance(owners,list) and len(owners)==len(source)and [v['selector']for v in owners]==[v['selector']for v in source_nodes],'business-text-leaf-owner-coverage');text_nodes={}
 norm=lambda s:' '.join(s.split())
 for o in owners:
  need(isinstance(o,dict) and set(o)=={'selector','identity_badge_exemption','parts','pseudo'}and isinstance(o['parts'],list),'business-text-leaf-owner-shape');need(o['pseudo']=={'before':'none','after':'none'}or isinstance(o['pseudo'],dict) and set(o['pseudo'])=={'before','after'}and all(v in('none','normal','""',"''")for v in o['pseudo'].values()),'business-text-leaf-generated-paint');s=source[o['selector']];exemption=o['identity_badge_exemption'];need(exemption is None or exemption==o['selector']and any(b['selector']==exemption for b in g.get('supported_static_identity_transforms',[]))and not norm(s.get('name')or'')and all(p.get('kind')!='text'or not norm(p.get('text',''))for p in o['parts'])and all(not norm(n.get('name')or'')for n in s.get('children')or[]),'business-text-leaf-badge-exemption');children=s.get('children')or[];expected=[c['selector']for c in children];actual=[];indices=[];parts=[]
  for p in o['parts']:
   total_parts+=1;need(total_parts<=64,'business-text-leaf-parts-budget')
   need(isinstance(p,dict) and type(p.get('child_index'))is int and p['child_index']>=0 and p['child_index']<64,'business-text-leaf-child-index');indices.append(p['child_index'])
   if p.get('kind')=='element':
    need(set(p)=={'kind','child_index','selector'}and p['selector']in source,'business-text-leaf-child-binding');actual.append(p['selector']);parts.append(source[p['selector']].get('name')or'')
   else:
    need(set(p)=={'kind','child_index','text'}and p.get('kind')=='text'and isinstance(p['text'],str)and len(p['text'].encode('utf-16-le'))//2<=16000,'business-text-leaf-text-shape');parts.append(p['text']);total_text+=len(p['text'].encode('utf-16-le'))//2;need(total_text<=16000,'business-text-leaf-text-budget')
    if norm(p['text']):text_nodes[(o['selector'],p['child_index'])]=p['text']
  expected_text=norm(s.get('name')or'');cursor=0;pending_space=False;pending_layout=False;previous_kind=None
  for part,value in zip(o['parts'],parts):
   if previous_kind=='element'or part['kind']=='element':pending_layout=True
   for ch in value:
    if ch.isspace():
     if cursor>0:pending_space=True
     continue
    if pending_space and cursor>0:need(expected_text[cursor:cursor+1]==' ','business-text-leaf-owner-aggregate');cursor+=1
    elif pending_layout and cursor>0 and expected_text[cursor:cursor+1]==' ':cursor+=1
    need(expected_text[cursor:cursor+1]==ch,'business-text-leaf-owner-aggregate');cursor+=1;pending_space=False;pending_layout=False
   previous_kind=part['kind']
  need(indices==sorted(set(indices))and actual==expected and cursor==len(expected_text),'business-text-leaf-owner-aggregate')
 need(text_nodes or all(not norm(n.get('name')or'')for n in source_nodes),'business-text-leaf-empty-source');leaves=leaf['leaves'];need(isinstance(leaves,list) and len(leaves)==len(text_nodes),'business-text-leaf-node-coverage');seen=set();units=rectangles=0;full=True;excerpt=True
 for l in leaves:
  need(isinstance(l,dict) and set(l)=={'owner_selector','child_index','segments','ancestors'},'business-text-leaf-shape');key=(l['owner_selector'],l['child_index']);need(key in text_nodes and key not in seen,'business-text-leaf-node-binding');seen.add(key);text=text_nodes[key];encoded=text.encode('utf-16-le');need(not any(ord(c)in(*range(0x202a,0x202f),*range(0x2066,0x206a),0x200b,0x200e,0x200f,0x2060,0xfeff)for c in text),'business-text-leaf-invisible-formatting')
  ancestors=l['ancestors'];need(isinstance(ancestors,list) and 1<=len(ancestors)<=40 and ancestors[0]['selector']==l['owner_selector']and want['selector']in [a['selector']for a in ancestors]and len({a['selector']for a in ancestors})==len(ancestors),'business-text-leaf-ancestor-binding')
  expected_chain=[l['owner_selector'],*reversed(source_ancestors[l['owner_selector']])];actual_chain=[a['selector']for a in ancestors]
  exact_chain=actual_chain[:len(expected_chain)]==expected_chain and actual_chain[len(expected_chain):]in([],['html'],['body','html'])
  root_body_alias=bool(expected_chain and expected_chain[-1]=='body'and source_context.get('body',{}).get('tag')=='body'and source_ancestors.get('body')==[]and actual_chain[:-2]==expected_chain[:-1]and actual_chain[-2:]==['html > body','html'])
  need(exact_chain or root_body_alias,'business-text-leaf-exact-source-ancestor-chain')
  for a in ancestors:
   need(isinstance(a,dict) and set(a)=={'selector','clip_source','ellipsis','x','y','box'}and isinstance(a['selector'],str)and type(a['x'])is bool and type(a['y'])is bool,'business-text-leaf-ancestor-schema');r=a['box'];need(isinstance(r,dict) and set(r)=={'left','top','right','bottom'}and all(type(v)in(int,float)and math.isfinite(v)for v in r.values())and r['right']>=r['left']and r['bottom']>=r['top'],'business-text-leaf-ancestor-box')
  for a in ancestors:need(a['box']==text_leaf_clip_box(a,source_context),'business-text-leaf-clip-box-derived')
  visible_any=False
  segments=l['segments'];need(isinstance(segments,list) and segments,'business-text-leaf-graphemes');cursor=0
  for seg in segments:
   need(isinstance(seg,dict) and set(seg)=={'start','end','rects'}and type(seg['start'])is int and type(seg['end'])is int and cursor<=seg['start']<seg['end']<=len(encoded)//2,'business-text-leaf-segment-order')
   try:gap=encoded[cursor*2:seg['start']*2].decode('utf-16-le');part=encoded[seg['start']*2:seg['end']*2].decode('utf-16-le')
   except UnicodeError:need(False,'business-text-leaf-surrogate-boundary')
   import unicodedata
   need(not all(unicodedata.category(ch).startswith('M')or unicodedata.category(ch)=='Cf'for ch in part),'business-text-leaf-grapheme-without-base')
   need(not norm(gap)and norm(part),'business-text-leaf-segment-coverage');cursor=seg['end'];units+=1;need(units<=512,'business-text-leaf-grapheme-budget');rs=seg['rects'];need(isinstance(rs,list) and rs,'business-text-leaf-segment-no-rect')
   for r in rs:
    r=box(r);rectangles+=1;need(rectangles<=2048,'business-text-leaf-rect-budget');complete=r['left']>=cell['left']and r['top']>=cell['top']and r['right']<=cell['right']and r['bottom']<=cell['bottom']and r['left']>=viewport['left']and r['top']>=viewport['top']and r['right']<=viewport['right']and r['bottom']<=viewport['bottom']
    visible=dict(r)
    for a in ancestors:
     b=a['box'];e=a['ellipsis'];need(isinstance(e,dict) and set(e)=={'text_overflow','line_clamp','overflow_x','overflow_y','client_width','client_height','scroll_width','scroll_height'}and all(isinstance(e[k],str)and len(e[k])<=100 for k in ('text_overflow','line_clamp','overflow_x','overflow_y'))and all(type(e[k])in(int,float)and math.isfinite(e[k])and e[k]>=0 for k in ('client_width','client_height','scroll_width','scroll_height')),'business-text-leaf-ellipsis-schema')
     if a['x']and(r['left']<b['left']or r['right']>b['right'])or a['y']and(r['top']<b['top']or r['bottom']>b['bottom']):complete=False
     need(e['text_overflow']==a['clip_source']['style']['textOverflow']and e['line_clamp']==a['clip_source']['style']['webkitLineClamp']and e['overflow_x']==a['clip_source']['style']['overflowX']and e['overflow_y']==a['clip_source']['style']['overflowY']and all(e[x]==a['clip_source']['metrics'][y]for x,y in [('client_width','clientWidth'),('client_height','clientHeight'),('scroll_width','scrollWidth'),('scroll_height','scrollHeight')]),'business-text-leaf-ellipsis-source');supported=(e['text_overflow']=='ellipsis'or re.fullmatch(r'[1-9][0-9]*',e['line_clamp'])is not None)and 'hidden'in(e['overflow_x'],e['overflow_y'])and(e['scroll_width']>e['client_width']or e['scroll_height']>e['client_height'])
     if supported:full=False
     if supported:
      if a['x']:visible['left']=max(visible['left'],b['left']);visible['right']=min(visible['right'],b['right'])
      if a['y']:visible['top']=max(visible['top'],b['top']);visible['bottom']=min(visible['bottom'],b['bottom'])
     elif a['x']and(visible['left']<b['left']or visible['right']>b['right'])or a['y']and(visible['top']<b['top']or visible['bottom']>b['bottom']):excerpt=False
    if visible['right']>visible['left']and visible['bottom']>visible['top']:
     visible_any=True
     if not(visible['left']>=cell['left']and visible['top']>=cell['top']and visible['right']<=cell['right']and visible['bottom']<=cell['bottom']and visible['left']>=viewport['left']and visible['top']>=viewport['top']and visible['right']<=viewport['right']and visible['bottom']<=viewport['bottom']):excerpt=False
    full=full and complete
  if not visible_any:excerpt=False
  need(not norm(encoded[cursor*2:].decode('utf-16-le')),'business-text-leaf-trailing-coverage')
 need(seen==set(text_nodes)and leaf['full']==full and leaf['excerpt_eligible']==excerpt,'business-text-leaf-derived-full');return full,excerpt

def validate_geometry(g,*,allow_ellipsis,selectors,identity_badges=(),manual=False):
 flags=('rendered','box_viewport_contained','unsupported_css_absent','text_unclipped','ellipsis_supported','evidence_eligible','preview_required','occlusion_verified')
 overflow=g.get('unresolved_own_text_overflow') if isinstance(g,dict) else None
 if overflow is not None:need(manual and allow_ellipsis and isinstance(overflow,list) and 1<=len(overflow)<=16,'business-own-text-manual-only')
 need(isinstance(g,dict) and set(g)-({'text_leaf_evidence'} if 'text_leaf_evidence'in g else set())-({'unresolved_own_text_overflow'} if overflow is not None else set()) in (set(flags)|{'text_clips'},set(flags)|{'text_clips','unsupported_css_diagnostic'},set(flags)|{'text_clips','unsupported_css_diagnostic','supported_static_identity_transforms','recursive_unsupported_css_absent'}) and all(type(g.get(k)) is bool for k in flags) and g['occlusion_verified'] is False,'business-geometry-flags-invalid')
 if 'unsupported_css_diagnostic' in g:
  diag=g['unsupported_css_diagnostic'];need(set(diag)=={'purpose','candidates','candidate_count','truncated'} and diag['purpose']=='readonly-unsupported-css-diagnostic-only' and type(diag['candidate_count']) is int and isinstance(diag['candidates'],list) and 0<=len(diag['candidates'])<=12 and diag['candidate_count']>=len(diag['candidates']) and diag['truncated']==(diag['candidate_count']>len(diag['candidates'])) ,'business-unsupported-css-diagnostic-invalid')
  for candidate in diag['candidates']:
   need(set(candidate)=={'selector','tag','relation','reasons','style','animations','animation_count','animations_truncated'} and (candidate['selector'] is None or isinstance(candidate['selector'],str) and len(candidate['selector'])<=1500) and candidate['relation'] in ('target','descendant','ancestor') and isinstance(candidate['reasons'],list) and bool(candidate['reasons']) and all(k in ('transform','zoom','clip','clipPath','maskImage','webkitMaskImage','filter','opacity','contentVisibility','active-or-pending-animation') for k in candidate['reasons']) and len(candidate['animations'])<=8 and all(isinstance(v,str) and len(v)<=160 for v in candidate['style'].values()),'business-unsupported-css-candidate-invalid')
 if 'supported_static_identity_transforms' in g:
  supported=g['supported_static_identity_transforms'];diag=g['unsupported_css_diagnostic'];need(isinstance(supported,list) and len(supported)<=12 and type(g['recursive_unsupported_css_absent']) is bool and g['recursive_unsupported_css_absent']==(diag['candidate_count']==0),'business-identity-transform-raw-css-conflict')
  for item in supported:
   need(isinstance(item,dict) and set(item)=={'selector','class','child_selector','child_class','classification','computed_transform','identity_components','active_or_pending_animation_count','text_present','interactive','geometry_changed','original_css_retained'} and {k:item.get(k) for k in ('selector','class','child_selector','child_class')} in identity_badges,'business-identity-badge-not-this-source-cell')
   c=gp.one([c for c in diag['candidates'] if c['selector']==item['selector']],'business-identity-transform-diagnostic');value=item.get('computed_transform');match=re.fullmatch(r'matrix\(([^()]*)\)',value) if isinstance(value,str) else None
   need(match is not None,'business-identity-transform-matrix-required');parts=[p.strip() for p in match[1].split(',')];need(len(parts)==6 and all(re.fullmatch(r'[-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:e[-+]?[0-9]+)?',p,re.I) for p in parts) and [float(p) for p in parts]==[1,0,0,1,0,0],'business-identity-transform-nonidentity')
   need(c['tag']=='sup' and c['relation']=='descendant' and c['reasons']==['transform'] and c['animation_count']==0 and c['style']['transform']==value and isinstance(item['identity_components'],list) and len(item['identity_components'])==6 and all(type(v) in (int,float) and math.isfinite(v) for v in item['identity_components']) and item['identity_components']==[1,0,0,1,0,0] and item['classification']=='reviewed-static-identity-2d-badge-v1' and type(item['active_or_pending_animation_count']) is int and item['active_or_pending_animation_count']==0 and item['text_present'] is False and item['interactive'] is False and item['geometry_changed'] is False and item['original_css_retained'] is True,'business-identity-transform-evidence-invalid')
  need(len({i['selector'] for i in supported})==len(supported) and g['unsupported_css_absent']==(g['recursive_unsupported_css_absent'] or not diag['truncated'] and diag['candidate_count']>0 and diag['candidate_count']==len(supported)),'business-identity-transform-supported-css-conflict')
 elif 'unsupported_css_diagnostic' in g:need(g['unsupported_css_absent']==(g['unsupported_css_diagnostic']['candidate_count']==0),'business-unsupported-css-diagnostic-conflict')
 clips=g.get('text_clips');need(isinstance(clips,list) and len(clips)<=64,'business-text-clip-evidence-invalid')
 need(g['text_unclipped']==(len(clips)==0 and not overflow and ('text_leaf_evidence'not in g or g['text_leaf_evidence']['full'])) and g['ellipsis_supported']==(all(x.get('supported') is True for x in clips) and not overflow and ('text_leaf_evidence'not in g or g['text_leaf_evidence']['excerpt_eligible'])),'business-text-clip-consistency-invalid')
 for clip in clips:
  need(set(clip)=={'selector','supported','text_overflow','line_clamp','overflow_x','overflow_y','client_width','client_height','scroll_width','scroll_height'} and isinstance(clip['selector'],str) and type(clip['supported']) is bool,'business-text-clip-fields-invalid')
  need(clip['selector'] in selectors and all(type(clip[k]) in (int,float) and math.isfinite(clip[k]) and clip[k]>=0 for k in ('client_width','client_height','scroll_width','scroll_height')),'business-clip-not-this-public-subtree-or-nonfinite')
  need(all(isinstance(clip[k],str) and len(clip[k])<=100 for k in ('text_overflow','line_clamp','overflow_x','overflow_y')),'business-clip-style-invalid')
  known=(clip['text_overflow']=='ellipsis' or re.fullmatch(r'[1-9][0-9]*',str(clip['line_clamp'])) is not None) and ('hidden' in (clip['overflow_x'],clip['overflow_y']))
  overflow=clip['scroll_width']>clip['client_width'] or clip['scroll_height']>clip['client_height'];need(clip['supported']==bool(known and overflow),'business-ellipsis-not-public-css')
 eligible=g['rendered'] and g['box_viewport_contained'] and g['unsupported_css_absent'] and (g['text_unclipped'] or allow_ellipsis and g['ellipsis_supported'])
 need(g['evidence_eligible']==eligible and g['preview_required']==(eligible and not g['text_unclipped']),'business-eligibility-inconsistent')

PARTIAL='partial-cell-original-clip-preview-v1'
def _box(value):
 need(isinstance(value,dict) and set(value)=={'left','top','right','bottom','width','height'} and all(type(v) in (int,float) and math.isfinite(v) for v in value.values()) and value['width']==value['right']-value['left']>0 and value['height']==value['bottom']-value['top']>0,'business-partial-box-invalid');return value
def _clip_box(value):
 # Renderer overflowClipBox returns edges only. This adapter is clip-only;
 # raw/visible rectangles still require all six exact finite fields in _box.
 need(isinstance(value,dict) and set(value)=={'left','top','right','bottom'} and all(type(v) in (int,float) and math.isfinite(v) for v in value.values()),'business-manual-clip-box-invalid')
 return _box({**value,'width':value['right']-value['left'],'height':value['bottom']-value['top']})
def _inside(a,b):return a['left']>=b['left'] and a['top']>=b['top'] and a['right']<=b['right'] and a['bottom']<=b['bottom']
def validate_partial_previews(base,source_spec=None):
 """Side proof only. Never changes any legacy geometry flag or raw source TD."""
 candidates=base.get('partial_cell_previews',[]);need(isinstance(candidates,list) and len(candidates)<=len(base['business_cells']),'business-partial-candidates-invalid');out={}
 for p in candidates:
  need(base.get('diagnostic_build') in ('viewport-notice-business-cells-v6','viewport-notice-business-cells-v7','viewport-notice-business-cells-v8','viewport-notice-business-cells-v9-provider-manual-preview-v2','viewport-notice-business-cells-v12-rectification-projection-v3','viewport-notice-business-cells-v13-fractional-auto-padding-v1') and (set(p)-{'preserved_ancestor_shadows'})=={'contract','notice_id','tr_selector','container_selector','device_pixel_ratio','container_metrics','cells','original_full_flags_unchanged','quality_review_required','text_unclipped','original_pixels_preserved'} and p['contract']==PARTIAL and p['original_full_flags_unchanged'] is True and p['quality_review_required'] is True and p['text_unclipped'] is False and p['original_pixels_preserved'] is True,'business-partial-contract-invalid')
  row=gp.one([r for r in base['business_cells'] if r['notice_id']==p['notice_id']],'partial-source-row');need(row['tr_selector']==p['tr_selector'] and p['notice_id'] not in out and len(p['cells'])==5,'business-partial-source-row-changed')
  need(source_spec is None or p['container_selector'] in source_spec['partial_source']['containers'],'business-partial-container-not-source');need(type(p['device_pixel_ratio']) in (int,float) and math.isfinite(p['device_pixel_ratio']) and .25<=p['device_pixel_ratio']<=16,'business-partial-dpr-invalid');m=p['container_metrics'];pr=_box(m['rect']);s=m['style'];need(s['overflowX']==s['overflowY']=='auto' and m['clientLeft']==m['clientTop']==0 and m['clientHeight']==m['offsetHeight']==m['scrollHeight'] and abs(pr['height']-m['clientHeight'])<=.5 and abs(pr['width']-m['clientWidth'])<=.5 and all(s[k]=='0px' for k in ('borderTopWidth','borderRightWidth','borderBottomWidth','borderLeftWidth','paddingTop','paddingRight','paddingBottom','paddingLeft')),'business-partial-container-invalid')
  bottom=pr['top']+m['clientHeight'];total_text=total_paint=0
  for i,(c,want) in enumerate(zip(p['cells'],row['cells'])):
   need(set(c)=={'index','field','selector','raw_box','visible_box','ancestor_clips','omitted_bottom_css_px','text_ranges','paint_bounds','structural_omissions','platform_label_clips','supported_ellipsis_selectors','text_complete_in_image'} and c['index']==i and all(c[k]==want[k] for k in ('field','selector')) and c['text_complete_in_image'] is False and want['geometry']['rendered'] is True and want['geometry']['unsupported_css_absent'] is True and want['geometry']['box_viewport_contained'] is False and want['geometry']['evidence_eligible'] is False,'business-partial-source-cell-invalid')
   raw=_box(c['raw_box']);v=_box(c['visible_box']);need(v['left']==raw['left'] and v['right']==raw['right'] and v['top']==raw['top'] and v['bottom']==bottom<raw['bottom'] and c['omitted_bottom_css_px']==raw['bottom']-bottom and 0<c['omitted_bottom_css_px']<=.5,'business-partial-not-original-bottom-strip')
   need(isinstance(c['ancestor_clips'],list) and any(a['selector']==p['container_selector'] and _box(a['box'])['bottom']==bottom for a in c['ancestor_clips']),'business-partial-container-clip-missing')
   for a in c['ancestor_clips']:need(_inside(v,_box(a['box'])),'business-partial-visible-intersection-invalid')
   source_nodes=source_spec['partial_source']['nodes'][want['selector']] if source_spec else None;node_map={n['selector']:n for n in source_nodes} if source_nodes else None;labels=c['platform_label_clips'];need(isinstance(labels,list) and len(labels)<=1 and (i==2 or not labels),'business-partial-label-wrong-cell')
   for label in labels:
    need(set(label)=={'classification','selector','text','range','owner_box','visible_box','clipping_cell','first_character_range','own_ellipsis_active','text_complete_in_image','original_pixels_preserved'} and label['classification']=='platform-original-clipped-product-label-v1' and label['text']=='商品' and label['selector'] in want['text_selectors'] and label['clipping_cell']==c['selector'] and label['own_ellipsis_active'] is False and label['text_complete_in_image'] is False and label['original_pixels_preserved'] is True,'business-partial-label-proof-invalid')
    
    if node_map is not None:
     node=node_map.get(label['selector']);need(node is not None and node['tag']=='span' and node['name']=='商品' and not node.get('children') and node['attributes'].get('class')=='governance_merchant-tag governance_merchant-tag-size-sm governance_merchant-tag-default-light tag-pd6WUO' and any(n['attributes'].get('class')=='title-AbHLxL' and (n.get('children') or [])[-1]['selector']==node['selector'] and len(n.get('children') or [])==2 and (n.get('children') or [])[0].get('attributes',{}).get('class')=='overhide-dQaf8m' for n in source_nodes),'business-partial-label-not-source-structure')
    r=_box(label['range']);lv=_box(label['visible_box']);owner=_box(label['owner_box']);first=_box(label['first_character_range']);need(_inside(r,owner) and r['left']>=raw['left'] and r['left']<raw['right']<r['right'] and r['top']>=v['top'] and r['bottom']<=v['bottom'] and lv==dict(r,right=v['right'],width=v['right']-r['left']) and _inside(first,v) and _inside(first,r),'business-partial-label-not-original-right-fragment')
   texts=c['text_ranges'];paints=c['paint_bounds'];need(isinstance(texts,list) and bool(texts) and isinstance(paints,list),'business-partial-public-content-required');total_text+=len(texts);total_paint+=len(paints);need(total_text<=1024 and total_paint<=128,'business-partial-public-proof-limit')
   for t in texts:
    need(set(t)=={'owner_selector','child_index','text_length','original_range','visible_range','classification'} and t['owner_selector'] in want['text_selectors'] and type(t['child_index']) is int and t['child_index']>=0 and type(t['text_length']) is int and 0<t['text_length']<=16000 and t['classification'] in ('unclipped','active-own-ellipsis','platform-original-clipped-label'),'business-partial-text-binding-invalid')
    original=_box(t['original_range']);vr=_box(t['visible_range']);need(_inside(vr,v) and _inside(vr,original),'business-partial-business-text-lost')
    if t['classification']=='unclipped':need(vr==original,'business-partial-unclipped-text-changed')
    elif t['classification']=='platform-original-clipped-label':need(any(l['selector']==t['owner_selector'] and l['range']==original and l['visible_box']==vr for l in labels),'business-partial-label-range-unbound')
    else:need(bool(c['supported_ellipsis_selectors']) and all(selector in want['text_selectors'] and any(x['selector']==selector and x['supported'] for x in want['geometry']['text_clips']) for selector in c['supported_ellipsis_selectors']),'business-partial-ellipsis-not-source-css')
   if node_map is not None:
    leafs={n['selector'] for n in source_nodes if n.get('name') and not n.get('children') and n.get('tag') not in ('img','svg','path','g','input','textarea','select')};need(leafs.issubset({t['owner_selector'] for t in texts}),'business-partial-source-text-not-measured')
   for paint in paints:
    need(node_map is None or paint['selector'] in node_map,'business-partial-paint-not-source')
    need(set(paint) in ({'selector','kind','bounds'},{'selector','kind','bounds','original_clip'}) and paint['kind'] in ('IMG','SVG','SVG-descendant','CSS-box','platform-label-background') and isinstance(paint['selector'],str),'business-partial-paint-invalid');b=_box(paint['bounds'])
    if paint.get('original_clip'):need(paint['kind']=='platform-label-background' and any(l['selector']==paint['selector'] and l['owner_box']==b for l in labels),'business-partial-unknown-original-paint-clip')
    else:need(_inside(b,v),'business-partial-business-paint-lost')
   structure=c['structural_omissions'];need(len(structure)==1 and structure[0]['selector']==c['selector'] and structure[0]['classification']=='cropped-uniform-cell-background-and-border' and structure[0]['omitted_bottom_css_px']==c['omitted_bottom_css_px'] and isinstance(structure[0]['background_color'],str),'business-partial-structural-omission-unreported')
   borders=structure[0]['borders'];need(set(borders)=={'top','right','bottom','left'},'business-partial-structural-borders-missing')
   for border in borders.values():need(set(border)=={'width','style','color'} and isinstance(border['color'],str) and len(border['color'])<=100 and (border['style']=='none' or border['width']=='0px' or border['style']=='solid' and re.fullmatch(r'\d+(?:\.\d{1,6})?px',border['width']) is not None and float(border['width'][:-2])*p['device_pixel_ratio']<=1+.5e-6*p['device_pixel_ratio']+1e-12),'business-partial-structural-border-unverified')
   for x in want['geometry']['text_clips']:need(x['supported'] or i==2 and x['selector']==c['selector'] and len(labels)==1,'business-partial-unexplained-overflow')
  shadows=p.get('preserved_ancestor_shadows',[]);need(isinstance(shadows,list) and len(shadows)<=1,'business-partial-ancestor-shadows-invalid')
  for shadow in shadows:
   need(base.get('diagnostic_build') in ('viewport-notice-business-cells-v7','viewport-notice-business-cells-v8','viewport-notice-business-cells-v12-rectification-projection-v3','viewport-notice-business-cells-v13-fractional-auto-padding-v1'),'business-partial-shadow-version-required')
   need(set(shadow)=={'other_public_effects','animations','classification','selector','tag','box_shadow','inset','bounds','radii','borders','safe_box','contains_all_five_raw_cells','original_pixels_preserved','visual_review_required'} and shadow['classification']=='observed-outer-ancestor-shadow-outside-business-crop-v1' and shadow['selector']=='#main-app > section > section' and shadow['tag']=='section' and shadow['box_shadow']=='rgba(0, 104, 173, 0.04) -8px 0px 40px 0px' and shadow['inset'] is False and all(shadow[k] is True for k in ('contains_all_five_raw_cells','original_pixels_preserved','visual_review_required')),'business-partial-ancestor-shadow-not-observed')
   need(source_spec is None or source_spec['partial_source']['structural_ancestors'].get(shadow['selector'],{}).get('tag')=='section' and row['tr_selector'] in source_spec['partial_source']['structural_ancestors'][shadow['selector']]['rows'],'business-partial-shadow-not-source-ancestor');effects=shadow['other_public_effects'];need(set(effects)=={'transform','zoom','clip','clipPath','maskImage','webkitMaskImage','filter','opacity','backdropFilter','borderImageSource','mixBlendMode','webkitBoxReflect','textShadow','outlineStyle','outlineWidth'} and all(isinstance(v,str) and len(v)<=240 for v in effects.values()),'business-partial-ancestor-effects-missing')
   need(all(effects[k] in ('','none') for k in ('transform','clipPath','maskImage','webkitMaskImage','filter','backdropFilter','borderImageSource','webkitBoxReflect','textShadow')) and effects['zoom'] in ('','1','normal') and effects['clip'] in ('','auto') and effects['opacity']=='1' and effects['mixBlendMode'] in ('','normal') and (effects['outlineStyle'] in ('','none') or effects['outlineWidth']=='0px'),'business-partial-ancestor-other-effects')
   need(isinstance(shadow['animations'],list) and len(shadow['animations'])<=8 and all(set(a)=={'pending','play_state'} and a['pending'] is False and a['play_state'] in ('finished','idle') for a in shadow['animations']),'business-partial-ancestor-motion')
   bounds=_box(shadow['bounds']);safe=_box(shadow['safe_box']);radii=shadow['radii'];borders=shadow['borders'];need(set(radii)=={'TopLeft','TopRight','BottomRight','BottomLeft'} and set(borders)=={'Top','Right','Bottom','Left'},'business-partial-ancestor-corners-missing')
   for r in radii.values():
    need(set(r)=={'raw','x','y'} and isinstance(r['raw'],str),'business-partial-ancestor-radius-invalid');parts=r['raw'].split();need(len(parts) in (1,2) and all(re.fullmatch(r'(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)px',part) for part in parts) and type(r['x']) in (int,float) and type(r['y']) in (int,float) and r['x']==float(parts[0][:-2]) and r['y']==float(parts[-1][:-2]),'business-partial-ancestor-radius-unproven')
   for border in borders.values():need(set(border)=={'raw','width'} and isinstance(border['raw'],str) and re.fullmatch(r'(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)px',border['raw']) is not None and type(border['width']) in (int,float) and border['width']==float(border['raw'][:-2]),'business-partial-ancestor-border-unproven')
   expected={'left':bounds['left']+max(radii['TopLeft']['x'],radii['BottomLeft']['x'],borders['Left']['width']),'right':bounds['right']-max(radii['TopRight']['x'],radii['BottomRight']['x'],borders['Right']['width']),'top':bounds['top']+max(radii['TopLeft']['y'],radii['TopRight']['y'],borders['Top']['width']),'bottom':bounds['bottom']-max(radii['BottomLeft']['y'],radii['BottomRight']['y'],borders['Bottom']['width'])};expected.update(width=expected['right']-expected['left'],height=expected['bottom']-expected['top']);need(safe==expected and all(_inside(c['raw_box'],safe) for c in p['cells']),'business-partial-ancestor-shadow-crop-not-safe')
  out[p['notice_id']]=p
 return out
def validate_manual_previews(base,source_spec=None):
 need(base.get('preview_contract')==MANUAL and base.get('hash_contract')==gp.projection_schema(command_projection({'elements':base.get('elements',[])}),True),'business-manual-contract-required');out={}
 view=base.get('manual_preview_viewport',{});need(set(view)=={'width','height'} and all(type(v) in (int,float) and math.isfinite(v) and v>0 for v in view.values()),'business-manual-viewport-invalid')
 candidates=base.get('manual_local_previews');need(isinstance(candidates,list) and len(candidates)<=len(base['business_cells']),'business-manual-candidates-invalid')
 for p in candidates:
  need(set(p)=={'contract','notice_id','tr_selector','cells','original_full_flags_unchanged','decorative_paint','quality_review_required','coverage_certified'} and p['contract']==LOCAL and p['quality_review_required'] is True and p['original_full_flags_unchanged'] is True and p['coverage_certified'] is False and p['decorative_paint']=='unresolved','business-manual-no-automatic-certification')
  row=gp.one([r for r in base['business_cells'] if r['notice_id']==p['notice_id']],'manual-source-row');need(p['notice_id'] not in out and row['tr_selector']==p['tr_selector'] and len(p['cells'])==5,'business-manual-five-source-cells-required')
  for i,(c,want) in enumerate(zip(p['cells'],row['cells'])):
   need(set(c)=={'index','field','selector','raw_box','visible_box','ancestor_clips','text_complete_in_image'} and c['index']==i and c['field']==want['field'] and c['selector']==want['selector'] and c['text_complete_in_image'] is False and want['geometry']['rendered'] is True and want['geometry']['unsupported_css_absent'] is True,'business-manual-source-cell-changed')
   raw=_box(c['raw_box']);visible=_box(c['visible_box']);need(_inside(visible,raw) and visible['left']>=0 and visible['top']>=0,'business-manual-region-not-conservative');clips=c['ancestor_clips'];need(isinstance(clips,list) and len(clips)<=32,'business-manual-clip-limit')
   expected=dict(raw)
   # A viewport bound is also revalidated against the native region proof below.
   expected['left']=max(0,raw['left']);expected['top']=max(0,raw['top']);expected['right']=min(view['width'],raw['right']);expected['bottom']=min(view['height'],raw['bottom'])
   for clip in clips:
    need(set(clip)=={'selector','box','overflow_x','overflow_y'} and isinstance(clip['selector'],str) and 0<len(clip['selector'])<=1500 and (source_spec is None or clip['selector'] in source_spec['manual_source_ancestors'][c['selector']] or clip['selector'] in ('html','html > body') and 'body' in source_spec['manual_source_ancestors'][c['selector']]),'business-manual-clip-not-ancestor');b=_clip_box(clip['box'])
    if clip['overflow_x'] in ('hidden','clip','scroll','auto'):expected['left']=max(expected['left'],b['left']);expected['right']=min(expected['right'],b['right'])
    if clip['overflow_y'] in ('hidden','clip','scroll','auto'):expected['top']=max(expected['top'],b['top']);expected['bottom']=min(expected['bottom'],b['bottom'])
   need(visible['left']==expected['left'] and visible['top']==expected['top'] and visible['right']==expected['right'] and visible['bottom']==expected['bottom'],'business-manual-intersection-changed')
  out[p['notice_id']]=p
 return out

def validate_own_text_overflows(base,spec,previews):
 for row,want in zip(base['business_cells'],spec['rows']):
  for cell,source_cell in zip(row['cells'],want['cells']):
   records=cell['geometry'].get('unresolved_own_text_overflow',[])
   if not records:continue
   need(base['diagnostic_build'] in ('viewport-notice-business-cells-v11-manual-own-text-overflow-v2','viewport-notice-business-cells-v12-rectification-projection-v3','viewport-notice-business-cells-v13-fractional-auto-padding-v1') and row['notice_id'] in previews,'business-own-text-preview-required')
   preview=previews[row['notice_id']];boxes=[c['raw_box'] for c in preview['cells']];union={'left':min(b['left'] for b in boxes),'top':min(b['top'] for b in boxes),'right':max(b['right'] for b in boxes),'bottom':max(b['bottom'] for b in boxes)};union.update(width=union['right']-union['left'],height=union['bottom']-union['top']);own=boxes[cell['index']]
   for item in records:
    need(set(item)=={'classification','notice_id','tr_selector','union_box','diagnostic','original_rejection','quality_review_required','text_complete_in_image','coverage_certified'} and item['classification']=='source-own-horizontal-text-overflow-v1' and item['notice_id']==row['notice_id'] and item['tr_selector']==row['tr_selector'] and item['union_box']==union and item['quality_review_required'] is True and item['text_complete_in_image'] is False and item['coverage_certified'] is False,'business-own-text-source-or-flags-changed')
    d=item['diagnostic'];need(d.get('cell_client_rects')==[own] and d.get('cell_client_rect_count')==1 and d.get('view')=={'left':0,'top':0,'right':base['manual_preview_viewport']['width'],'bottom':base['manual_preview_viewport']['height'],'width':None,'height':None},'business-own-text-cell-or-view-changed');need(d.get('schema')=='business-text-geometry-failure-v1' and d.get('build')==base['diagnostic_build'] and d.get('truncated') is False and d.get('capture_certified') is False and d.get('geometry_decision_changed') is False and d.get('pixel_input_actions') is False and d.get('cell')=={'selector':cell['selector'],'tag':'td'} and d.get('node',{}).get('selector') in source_cell['text_selectors'] and d['node']['selector']!=cell['selector'],'business-own-text-not-source-descendant')
    t=d['text_rect'];need(set(t)=={'left','top','right','bottom','width','height'} and all(type(t[k]) in (int,float) and math.isfinite(t[k]) for k in ('left','top','right','bottom')),'business-own-text-nonfinite');t={k:t[k] for k in ('left','top','right','bottom')};need(t['right']>t['left'] and t['bottom']>t['top'] and _inside(t,union) and t['top']>=own['top'] and t['bottom']<=own['bottom'] and (t['left']<own['left'] or t['right']>own['right']) and t['left']>=0 and t['top']>=0 and t['right']<=base['manual_preview_viewport']['width'] and t['bottom']<=base['manual_preview_viewport']['height'],'business-own-text-outside-business-union')
    if item['original_rejection']=='business-text-geometry-unreviewed':need(d['failed_conditions']=={'non_positive':False,'outside_view':False,'outside_cell':True},'business-own-text-failure-changed')
    else:need(item['original_rejection']=='business-text-ancestor-clip-unreviewed' and d['failed_conditions']=={'ancestor_clip_x':True,'ancestor_clip_y':False} and d.get('ancestor',{}).get('selector')==cell['selector'],'business-own-text-other-ancestor-clip')

def selectable_rows(base):
 rows=base['business_cells']
 if base.get('diagnostic_build')=='viewport-notice-business-cells-v13-fractional-auto-padding-v1':rows=[r for r in rows if all(c['geometry'].get('text_leaf_evidence',{}).get('excerpt_eligible')is True for c in r['cells'])]
 if base.get('preview_contract')==MANUAL:
  selected=validate_manual_previews(base);return [r for r in rows if r['notice_id'] in selected]
 partial=validate_partial_previews(base)
 return [r for r in rows if all(c['geometry']['evidence_eligible'] for c in r['cells']) or r['notice_id'] in partial]

def manual_date_fragment(base):
 if base.get('preview_contract')!=MANUAL:return False
 d=base['business_date'];g=d['geometry'];clips=g.get('text_clips',[])
 if not (g['rendered'] is True and g['box_viewport_contained'] is True and g['unsupported_css_absent'] is True and g['text_unclipped'] is False and g['evidence_eligible'] is False and len(clips)==1):return False
 c=clips[0]
 return c['selector']==d['selector'] and c['supported'] is False and c['text_overflow']=='clip' and c['line_clamp']=='none' and c['overflow_x']==c['overflow_y']=='clip' and all(type(c[k]) in (int,float) and math.isfinite(c[k]) and c[k]>0 for k in ('client_width','client_height','scroll_width','scroll_height')) and c['scroll_width']>c['client_width'] and c['scroll_height']==c['client_height']

def prepare_region_request(inputs,p,mode,*,notice_ids=None):
 validate_base(p,inputs);need(mode in ('anchor','rows'),'business-frame-mode-invalid')
 if mode=='anchor':
  need(notice_ids is None,'business-anchor-cannot-select-notices');need((p['business_date']['geometry']['evidence_eligible'] or inputs.get('screenshot_identity') is not None and manual_date_fragment(p)) and all(h['geometry']['evidence_eligible'] for h in p['business_headers']),'business-date-and-five-labels-not-eligible');selectors=[p['business_date']['selector'],*[h['selector'] for h in p['business_headers']]]
 else:
  rows=selectable_rows(p)
  if notice_ids is not None:
   need(isinstance(notice_ids,list) and bool(notice_ids) and len(notice_ids)==len(set(notice_ids)),'business-explicit-notice-selection-invalid');rows=[r for r in rows if r['notice_id'] in notice_ids];need([r['notice_id'] for r in rows]==notice_ids,'business-notice-selection-not-original-eligible-order')
  need(rows,'business-no-complete-five-cell-group');selectors=[c['selector'] for r in rows for c in r['cells']]
 need(len(selectors)==len(set(selectors)),'business-selector-duplicate');c=inputs['command'];return {'op':'dom-region-proof',**{k:c[k] for k in ('tabId','windowId','groupid')},'base':c,'selectors':selectors,'purpose':'evidence-crop-only'}

def validate_table_seams(seams,base,selectors,*,allow_border=False):
 need(isinstance(seams,list) and len(seams)<=50,'business-seam-evidence-invalid');rows=base['business_cells'];indices={r['notice_id']:i for i,r in enumerate(rows)};seen=set()
 for seam in seams:
  need((set(seam)=={'classification','foreign_notice_id','foreign_row','foreign_selector','tag','tolerance_css_px','original_pixels_preserved','matches'} or allow_border and set(seam)=={'classification','foreign_notice_id','foreign_row','foreign_selector','tag','tolerance_css_px','original_pixels_preserved','matches','preserved_border'}) and seam['classification']=='verified-adjacent-table-float-seam-v1' and seam['tolerance_css_px']==2**-15 and seam['original_pixels_preserved'] is True and seam['foreign_notice_id'] in indices,'business-seam-contract-invalid')
  index=indices[seam['foreign_notice_id']];row=rows[index];need(seam['foreign_row']==row['tr_selector'] and seam['tag'] in ('TR','TD') and seam['foreign_selector'] in ([row['tr_selector']] if seam['tag']=='TR' else [c['selector'] for c in row['cells']]) and seam['foreign_selector'] not in seen,'business-seam-foreign-row-invalid');seen.add(seam['foreign_selector']);need(isinstance(seam['matches'],list) and 1<=len(seam['matches'])<=100,'business-seam-matches-invalid')
  for match in seam['matches']:
   need(set(match)=={'selected_notice_id','selected_row','direction','overlap_css_px','row_overlap_css_px'} and match['selected_notice_id'] in indices,'business-seam-match-invalid');j=indices[match['selected_notice_id']];target=rows[j]
   need(abs(j-index)==1 and match['selected_row']==target['tr_selector'] and all(c['selector'] in selectors for c in target['cells']) and not any(c['selector'] in selectors for c in row['cells']) and match['direction']==('preceding-row-bottom' if index<j else 'following-row-top'),'business-seam-not-adjacent-selected-row')
   need(all(type(match[k]) in (int,float) and math.isfinite(match[k]) and 0<match[k]<=2**-15 for k in ('overlap_css_px','row_overlap_css_px')),'business-seam-overlap-out-of-bound')
  if 'preserved_border' in seam:
   border=seam['preserved_border'];need(allow_border and seam['tag']=='TD' and isinstance(border,dict) and set(border)=={'classification','side','borders','device_pixel_ratio','physical_width','maximum_physical_rounding_error','css_serialization_decimal_places','original_pixels_preserved','visual_review_required'} and border['classification']=='observed-adjacent-TD-single-physical-pixel-border-v1' and border['side'] in ('top','bottom') and type(border['device_pixel_ratio']) in (int,float) and math.isfinite(border['device_pixel_ratio']) and .25<=border['device_pixel_ratio']<=16 and border['css_serialization_decimal_places']==6 and border['maximum_physical_rounding_error']==.5e-6*border['device_pixel_ratio']+1e-12 and border['original_pixels_preserved'] is True and border['visual_review_required'] is True,'business-seam-border-contract-invalid')
   need(all(m['direction']==('preceding-row-bottom' if border['side']=='bottom' else 'following-row-top') for m in seam['matches']) and set(border['borders'])=={'top','right','bottom','left'},'business-seam-border-not-facing-neighbor')
   for side,b in border['borders'].items():
    need(isinstance(b,dict) and set(b)=={'style','width','color'},'business-seam-border-style-invalid')
    if side==border['side']:need(b['style']=='solid' and b['color']=='rgba(0, 24, 61, 0.08)' and isinstance(b['width'],str) and re.fullmatch(r'(?:0|[1-9][0-9]*)(?:\.[0-9]{1,6})?px',b['width']) is not None and 0<float(b['width'][:-2])<=4,'business-seam-border-not-observed-single-pixel')
    else:need((b['style']=='none' or b['width']=='0px') and isinstance(b['color'],str) and len(b['color'])<=100,'business-seam-border-other-edge-painted')
   need(type(border['physical_width']) in (int,float) and math.isfinite(border['physical_width']) and border['physical_width']==float(border['borders'][border['side']]['width'][:-2])*border['device_pixel_ratio'] and abs(border['physical_width']-1)<=border['maximum_physical_rounding_error'],'business-seam-border-not-one-physical-pixel')

def facts(p,inputs,selectors=None):
 """Only REGION-produced coverage is authoritative; base never counts a notice."""
 validate_base(p['base_proof'],inputs)
 if p['base_proof'].get('diagnostic_build')=='viewport-notice-business-cells-v13-fractional-auto-padding-v1':
  v=p['viewport'];bv=_box(p['base_proof']['business_viewport']);need(bv['left']==bv['top']==0 and bv['right']<=v['width']and bv['bottom']<=v['height'],'business-leaf-region-viewport-binding')
 if inputs.get('screenshot_identity') is not None:return manual_facts(p,inputs,selectors)
 need(p.get('region_build') in ('region-notice-business-cells-v1','region-notice-business-cells-v2','region-notice-business-cells-v3','region-notice-business-cells-v4','region-notice-business-cells-v5','region-notice-business-cells-v6','region-notice-business-cells-v7') and p.get('method')=='public-DOM-evidence-region-proof' and p.get('geometry_purpose')=='evidence-crop-only' and p.get('pixel_input_actions') is False and p.get('occlusion_verified') is False and type(p.get('quality_review_required')) is bool,'business-region-real-paint-proof-required')
 audit=p.get('paint_audit',{});seams=p.get('adjacent_table_seams',[])
 if p.get('region_build') in ('region-notice-business-cells-v4','region-notice-business-cells-v5','region-notice-business-cells-v6','region-notice-business-cells-v7'):
  validate_table_seams(seams,p['base_proof'],p['selectors'],allow_border=p['region_build'] in ('region-notice-business-cells-v5','region-notice-business-cells-v6','region-notice-business-cells-v7'));need(not any(s.get('preserved_border') for s in seams) or p.get('quality_review_required') is True,'business-seam-border-requires-preview');need(audit.get('roundoff_count')==len(seams),'business-seam-count-invalid');audit={k:v for k,v in audit.items() if k!='roundoff_count'}
 else:need(not seams,'business-legacy-cannot-claim-seam')
 need(audit=={'contract':'public-DOM-business-paint-audit-v1','unpainted_count':len(p.get('unpainted_elements',[])),'preserved_count':len(p.get('preserved_translucent_backgrounds',[]))+len(p.get('preserved_table_shadows',[])),'unresolved_count':len(p.get('unresolved_overlay',[]))},'business-region-paint-audit-required')
 for shadow in p.get('preserved_table_shadows',[]):
  need(shadow.get('class')=='governance_merchant-Table-ColumnShadow governance_merchant-Table-ColumnShadow_end' and shadow.get('parent_class') in ('governance_merchant-Table-Shadow governance_merchant-Table-Shadow_head','governance_merchant-Table-Shadow governance_merchant-Table-Shadow_sticky') and shadow.get('container_class')=='governance_merchant-Table-Container governance_merchant-Table-Container_scrollable' and shadow.get('frame_class')=='governance_merchant-Table-Frame' and shadow.get('box_shadow')=='rgba(16, 17, 20, 0.08) -12px 0px 12px -12px, rgba(16, 17, 20, 0.04) -4px 0px 4px -4px, rgba(16, 17, 20, 0.08) -1px 0px 1px -1px' and shadow.get('classification')=='noninteractive-translucent-table-edge-shadow' and shadow.get('structure')=='governance-table-column-shadow-end-v1' and shadow.get('layer_alphas')==[.08,.04,.08] and shadow.get('composited_alpha_upper_bound')==1-(1-.08)*(1-.04)*(1-.08) and type(shadow.get('ancestor_opacity')) in (int,float) and 0<=shadow['ancestor_opacity']<=1 and shadow.get('effective_alpha_upper_bound')==shadow['composited_alpha_upper_bound']*shadow['ancestor_opacity'] and shadow.get('approved_alpha_limit')==.2 and shadow.get('effective_alpha_upper_bound')<=.2 and all(shadow.get(k) is True for k in ('original_pixels_preserved','visual_review_required','foreign_css_effects_absent_except_known_shadow')) and p.get('quality_review_required') is True,'business-table-shadow-evidence-invalid')
 for ignored in p.get('unpainted_elements',[]):need(ignored.get('classification')=='public-CSS-no-painted-content' and type(ignored.get('checked_nodes')) is int and 1<=ignored['checked_nodes']<=64 and all(ignored.get(k) is True for k in ('background_absent','borders_absent','shadows_absent','pseudo_absent','text_absent','images_absent','interactive_absent')),'business-unpainted-structure-unverified')
 need(p.get('evidence_contract')==CONTRACT and p.get('derived_business_coverage',{}).get('contract')==CONTRACT,'business-region-coverage-required');base=p['base_proof'];selected=p['selectors'];allowed=[base['business_date']['selector'],*[h['selector'] for h in base['business_headers']],*[c['selector'] for r in base['business_cells'] for c in r['cells']]];need(len(selected)==len(set(selected)) and all(s in allowed for s in selected),'business-foreign-region-selector');need(selectors is None or selected==selectors,'business-region-selectors-changed');coverage=p['derived_business_coverage'];wanted=[];fragments={};partial=validate_partial_previews(base,inputs['business_spec']);selected_partial=[]
 for row in base['business_cells']:
  seen=[c['selector'] in selected for c in row['cells']]
  if any(seen):
   candidate=partial.get(row['notice_id']);need(all(seen) and (all(c['geometry']['evidence_eligible'] for c in row['cells']) or candidate is not None),'business-partial-five-cells-no-coverage');wanted.append(row['notice_id']);fragments[row['notice_id']]=[{'field':c['field'],'text_complete_in_image':False if candidate else c['geometry']['text_unclipped']} for c in row['cells']]
   if candidate:selected_partial.append(candidate)
 date=base['business_date']['selector'] in selected;need(not date or base['business_date']['geometry']['evidence_eligible'],'business-date-not-eligible');heads=all(h['selector'] in selected and h['geometry']['evidence_eligible'] for h in base['business_headers']);need(coverage=={**({'capture_subcontract':PARTIAL,'partial_cell_original_clips':selected_partial} if selected_partial else {}),'contract':CONTRACT,'notice_ids':wanted,'date_filter_visible':date,'list_headers_visible':heads,'cell_text_completeness':fragments},'business-region-derived-coverage-changed')
 need(not any(not f['text_complete_in_image'] for fields in fragments.values() for f in fields) or p.get('quality_review_required') is True,'business-ellipsis-requires-preview')
 if selected_partial:
  need(not any(x.get('preserved_ancestor_shadows') for x in selected_partial) or p['region_build']=='region-notice-business-cells-v7','business-partial-shadow-region-version-required')
  need(p['region_build'] in ('region-notice-business-cells-v6','region-notice-business-cells-v7') and p['quality_review_required'] is True,'business-partial-preview-required');boxes=[c['visible_box'] for proof in selected_partial for c in proof['cells']];region=p['region'];need(all(_inside(b,_box(region)) for b in boxes),'business-partial-crop-loses-content')
  if len(selected)==len(boxes):need(region['left']==min(b['left'] for b in boxes) and region['right']==max(b['right'] for b in boxes) and region['top']==min(b['top'] for b in boxes) and region['bottom']==max(b['bottom'] for b in boxes),'business-partial-crop-not-conservative-union')
 if base.get('diagnostic_build')=='viewport-notice-business-cells-v13-fractional-auto-padding-v1'and not selected_partial and base.get('preview_contract')!=MANUAL:
  selected_cells=[c for r in base['business_cells']for c in r['cells']if c['selector']in p['selectors']]
  for c in selected_cells:need(_inside(_box(c['box']),bv)and _inside(_box(c['box']),_box(p['region'])),'business-leaf-cell-not-in-original-region')
  if selected_cells and len(selected_cells)==len(p['selectors'])and not selected_partial and base.get('preview_contract')!=MANUAL:
   boxes=[c['box']for c in selected_cells];need(p['region']=={'left':min(c['left']for c in boxes),'top':min(c['top']for c in boxes),'right':max(c['right']for c in boxes),'bottom':max(c['bottom']for c in boxes),'width':max(c['right']for c in boxes)-min(c['left']for c in boxes),'height':max(c['bottom']for c in boxes)-min(c['top']for c in boxes)},'business-leaf-exact-selected-cell-region-union')
 return {**({'capture_subcontract':PARTIAL,'partial_cell_original_clips':selected_partial} if selected_partial else {}),'date_filter_visible':date,'filters_visible':False,'visible_filter_kinds':['date-filter'] if date else [],'image_filter_coverage':'date-only' if date else 'none','list_headers_visible':heads,'notice_ids':wanted,'cell_text_completeness':fragments}

def request_base(inputs,request):
 reply=request(inputs['command']);need(reply.get('ok') is True,'business-base-request-failed:'+str(reply.get('error')));need(reply['result'].get('diagnostic_build')=='viewport-notice-business-cells-v13-fractional-auto-padding-v1','business-live-v13-producer-required');return validate_base(reply['result'],inputs)
def expected_visibility(mode,facts):
 if facts.get('capture_subcontract')==LOCAL:return {'capture_subcontract':LOCAL,'uncertified_local_preview_acknowledged':True,**({'unresolved_source_neighbor_overlap_acknowledged':True} if facts.get('unresolved_source_neighbor_overlap') else {}),**({'source_own_horizontal_text_overflow_acknowledged':True} if facts.get('unresolved_own_text_overflow') else {}),**({'original_platform_clipping_acknowledged':True} if mode=='rows' else {}),'unresolved_decorative_paint_acknowledged':True,'date_and_header_labels':mode=='anchor' and not facts.get('date_visible_fragment_in_image',False),**({'date_visible_fragment_in_image':True,'date_text_complete_in_image':False,'date_fragment_source_value':facts['date_fragment_source_value'],'five_header_labels_visible':True,'date_image_caption':'日期框仅可见片段；完整日期来自已核源值，不声称图中文字完整。'} if facts.get('date_visible_fragment_in_image') else {}),'rows':{notice:{f['field']:{'visible_fragment':True,'text_complete_in_image':False} for f in fields} for notice,fields in facts['cell_text_completeness'].items()}}
 return {**({'capture_subcontract':PARTIAL,'original_partial_cell_clip_acknowledged':True,'platform_label_text_incomplete_acknowledged':True,'structural_bottom_omissions_acknowledged':True,**({'structural_ancestor_shadow_preserved_acknowledged':True} if any(p.get('preserved_ancestor_shadows') for p in facts.get('partial_cell_original_clips',[])) else {})} if facts.get('capture_subcontract')==PARTIAL else {}),'date_and_header_labels':mode=='anchor','rows':{notice:{f['field']:{'visible_fragment':True,'text_complete_in_image':f['text_complete_in_image']} for f in fields} for notice,fields in facts['cell_text_completeness'].items()}}
def no_unresolved_navigation(source,capture_ref):
 """Original canonical navigation cannot be washed by a new capture profile."""
 from pathlib import Path
 import prepare_records_profile as producer
 import governance_detail as d
 capture=d.document(capture_ref);meta=capture['derivation']
 path=Path(source['path']).resolve().parent/'.records-region-navigation'/source['sha256']/'state.json'
 if meta.get('kind')=='governance-records-reboot-derived-profile-v1':
  import violation_reboot_profile as reboot
  path=reboot.nav_root(capture,source)/'state.json'
 need(path.exists(),'business-canonical-navigation-required');state=json.loads(path.read_text());binding=state.get('binding',{});navref=binding.get('profile');nav=d.document(navref);producer.validate(nav,source)
 need({k:v for k,v in nav.items() if k!='evidence_contract'}=={k:v for k,v in capture.items() if k!='evidence_contract'},'business-navigation-capture-profile-scope-changed')
 need(binding=={'schema':'records-region-navigation-v1','source':source,'profile':navref,'job':meta['job'],'query':meta['query'],'tab_id':meta['tab_id'],'window_id':meta['window_id']},'business-canonical-navigation-binding-changed')
 need(isinstance(state.get('operations'),list) and all(op.get('state')=='complete' for op in state['operations']),'business-canonical-navigation-unresolved')
 return state

def no_unknown_other_capture(source,chain_id):
 """Only the active source/chain's named owners can block a new capture."""
 from pathlib import Path
 import json
 need(isinstance(chain_id,str)and chain_id,'business-current-capture-chain-required')
 base=Path(source['path']).resolve().parent
 # Use the same fingerprint implementation as the actual capture owners.
 import frame_capture as fc
 name=fc.fingerprint([source['sha256'],chain_id])+'.json'
 for folder in ('.frame-capture-state','.native-frame-capture-state','.native-region-frame-state'):
  path=base/folder/name
  if not path.exists():continue
  state=json.loads(path.read_text());need(state.get('scope',{}).get('source_sha256')==source['sha256']and state['scope'].get('chain_id')==chain_id,'business-current-capture-owner-scope')
  need(all(f.get('state')=='complete'for f in state.get('frames',[])),'business-original-source-capture-unresolved-no-new-policy')

def make_command(source_ref,observation,elements,*,screenshot_identity=None,projection_contract=None):
 """Called only after the derived-profile source/query/current-page gate.
 TR aggregate names may be readTree-truncated; proof binds actual five TDs instead.
 """
 import verified_capture as vc
 source=vc.pinned(source_ref['path'],source_ref['sha256']);tree=observation['tree'];url=observation['tab']['url'] if screenshot_identity is not None else None;projection=gp.project(tree,str(source['groupid']),actual_url=url,projection_contract=projection_contract);ns=vc.allnodes(tree);out=[]
 need(source.get('capture_schema')=='governance-public-dom-capture-v1' and source.get('source')=='local-dom-bridge','business-actual-source-required')
 for item in elements:
  n=gp.one([n for n in ns if n.get('selector')==item['selector']],'business-command-selector')
  if item['kind']=='row':
   need(item['selector'] in projection['rows'] and projection['rows'][item['selector']][0]==item['notice_id'],'business-command-notice-conflict');text=gp.canonical(projection['rows'][item['selector']])
  elif item['kind']=='header':text=vc.explicit_header_text(n)
  else:need(item['kind']=='date-filter','business-command-kind');text=' '.join(str(n.get('attributes',{}).get('value',n.get('name',''))).split())
  out.append({'key':command_namespace(screenshot_identity is not None,projection_contract)+':'+item['key'],'kind':item['kind'],'locator':{'by':'selector','value':item['selector']},'notice_id':item['notice_id'],'expected_text':text})
 c={'op':'viewport-proof','tabId':observation['tab_id'],'windowId':observation['tab']['windowId'],'groupid':str(source['groupid']),'source_sha256':source_ref['sha256'],'dom_sha256':gp.digest(tree,str(source['groupid']),actual_url=url,projection_contract=projection_contract),'elements':out};vc.bridge.validate_command(c);return c


def manual_facts(p,inputs,selectors=None):
 need(p.get('region_build') in ('region-notice-business-cells-v8-manual-preview-v2','region-notice-business-cells-v9-manual-anchor-v2','region-notice-business-cells-v10-manual-anchor-hotfix-v2','region-notice-business-cells-v11-manual-neighbor-preview-v2','region-notice-business-cells-v12-manual-date-fragment-v2') and p.get('quality_review_required') is True and p.get('occlusion_verified') is False and p.get('manual_preview_unresolved') is True,'business-manual-region-must-await-visual-review')
 base=p['base_proof'];candidates=validate_manual_previews(base,inputs['business_spec']);selected=p['selectors'];need(selectors is None or selected==selectors,'business-manual-selectors-changed');need(len(selected)==len(set(selected)),'business-manual-duplicate-selector');wanted=[];fragments={};boxes=[]
 for row in base['business_cells']:
  seen=[c['selector'] in selected for c in row['cells']]
  if any(seen):
   need(all(seen) and row['notice_id'] in candidates,'business-manual-incomplete-five-cells');wanted.append(row['notice_id']);fragments[row['notice_id']]=[{'field':c['field'],'text_complete_in_image':False} for c in row['cells']];boxes += [c['visible_box'] for c in candidates[row['notice_id']]['cells']]
 anchors=[base['business_date'],*base['business_headers']];anchor_selectors=[a['selector'] for a in anchors];is_anchor=selected==anchor_selectors
 date_fragment=is_anchor and manual_date_fragment(base)
 if is_anchor:need(p.get('region_build') in ('region-notice-business-cells-v9-manual-anchor-v2','region-notice-business-cells-v10-manual-anchor-hotfix-v2','region-notice-business-cells-v11-manual-neighbor-preview-v2','region-notice-business-cells-v12-manual-date-fragment-v2') and not wanted and (base['business_date']['geometry']['evidence_eligible'] or date_fragment) and all(a['geometry']['evidence_eligible'] for a in base['business_headers']),'business-manual-date-and-headers-not-eligible')
 else:need(wanted and len(selected)==5*len(wanted) and not any(s in selected for s in anchor_selectors),'business-manual-only-source-five-cells')
 r=_box(p['region']);v=p['viewport'];need(r['left']>=0 and r['top']>=0 and r['right']<=v['width'] and r['bottom']<=v['height'],'business-manual-crop-outside-viewport')
 if not is_anchor:need(r['left']==min(b['left'] for b in boxes) and r['right']==max(b['right'] for b in boxes) and r['top']==min(b['top'] for b in boxes) and r['bottom']==max(b['bottom'] for b in boxes),'business-manual-crop-not-exact-intersection-union')
 date_fields={'date_visible_fragment_in_image':True,'date_text_complete_in_image':False,'date_fragment_source_value':base['business_date']['text']} if date_fragment else {}
 if date_fragment:need(p.get('region_build')=='region-notice-business-cells-v12-manual-date-fragment-v2','business-date-fragment-build-required')
 coverage={'contract':CONTRACT,'capture_subcontract':LOCAL,'notice_ids':wanted,'date_filter_visible':is_anchor and not date_fragment,'list_headers_visible':is_anchor,'cell_text_completeness':fragments,'coverage_certified':False,**date_fields}
 need(p.get('derived_business_coverage')==coverage,'business-manual-coverage-not-derived')
 neighbors=validate_source_neighbors(p,inputs,wanted)
 own_overflows=[item for row in base['business_cells'] if row['notice_id'] in wanted for cell in row['cells'] for item in cell['geometry'].get('unresolved_own_text_overflow',[])]
 return {**({'unresolved_own_text_overflow':own_overflows} if own_overflows else {}),**({'unresolved_source_neighbor_overlap':neighbors} if neighbors else {}),**date_fields,'capture_subcontract':LOCAL,'date_filter_visible':is_anchor and not date_fragment,'filters_visible':False,'visible_filter_kinds':['date-filter-fragment'] if date_fragment else ['date-filter'] if is_anchor else [],'image_filter_coverage':'date-fragment-only' if date_fragment else 'date-only' if is_anchor else 'none','list_headers_visible':is_anchor,'notice_ids':wanted,'cell_text_completeness':fragments}


def validate_source_neighbors(proof,inputs,wanted):
 neighbors=proof.get('unresolved_source_neighbor_overlap',[]);need(isinstance(neighbors,list) and len(neighbors)<=50,'business-source-neighbor-limit')
 if not neighbors:return []
 need(proof.get('external_painted_overlap')=='unresolved' and proof.get('paint_audit',{}).get('source_neighbor_unresolved_count')==len(neighbors),'business-source-neighbor-paint-must-remain-unresolved')
 need(proof.get('region_build') in ('region-notice-business-cells-v11-manual-neighbor-preview-v2','region-notice-business-cells-v12-manual-date-fragment-v2') and proof.get('quality_review_required') is True,'business-source-neighbor-preview-required')
 rows=inputs['business_spec']['rows'];byid={r['notice_id']:(i,r) for i,r in enumerate(rows)};seen=set()
 for n in neighbors:
  need(set(n)=={'contract','source_sha256','foreign_notice_id','foreign_row','foreign_selector','tag','table_selector','tbody_selector','foreign_rect','foreign_row_rect','matches','paint_status','original_pixels_preserved','visual_review_required','coverage_added'} and n['contract']=='unresolved-source-neighbor-overlap-v1' and n['source_sha256']==inputs['command']['source_sha256'] and n['paint_status']=='unresolved-source-row-paint' and n['original_pixels_preserved'] is True and n['visual_review_required'] is True and n['coverage_added'] is False,'business-source-neighbor-contract')
  need(n['foreign_notice_id'] in byid and n['foreign_notice_id'] not in wanted and n['foreign_selector'] not in seen,'business-source-neighbor-not-foreign');seen.add(n['foreign_selector']);i,row=byid[n['foreign_notice_id']];need(n['foreign_row']==row['tr_selector'] and n['tag'] in ('TR','TD') and n['foreign_selector'] in ([row['tr_selector']] if n['tag']=='TR' else [c['selector'] for c in row['cells']]),'business-source-neighbor-not-source-row')
  ancestors=inputs['business_spec']['manual_source_ancestors'][row['cells'][0]['selector']];need(len(ancestors)>=3 and n['table_selector']==ancestors[-3] and n['tbody_selector']==ancestors[-2] and ancestors[-1]==row['tr_selector'],'business-source-neighbor-not-source-table')
  r=_box(n['foreign_rect']);rr=_box(n['foreign_row_rect']);need(_inside(r,rr) and (n['tag']!='TR' or r==rr),'business-source-neighbor-rect-invalid');need(isinstance(n['matches'],list) and 1<=len(n['matches'])<=100,'business-source-neighbor-matches-invalid')
  for match in n['matches']:
   need(set(match)=={'selected_notice_id','selected_row','selected_source_index','foreign_source_index','selected_dom_row_index','foreign_dom_row_index','direction','selected_raw_row_rect','selected_visible_cell_rect'} and match['selected_notice_id'] in wanted,'business-source-neighbor-target-invalid');j,target=byid[match['selected_notice_id']];need(abs(j-i)==1 and match['selected_row']==target['tr_selector'] and type(match['selected_source_index']) is int and type(match['foreign_source_index']) is int and match['selected_source_index']==j and match['foreign_source_index']==i and type(match['selected_dom_row_index']) is int and type(match['foreign_dom_row_index']) is int and match['selected_dom_row_index']==j and match['foreign_dom_row_index']==i and match['direction']==('preceding-row-bottom' if i<j else 'following-row-top'),'business-source-neighbor-not-adjacent')
   target_ancestors=inputs['business_spec']['manual_source_ancestors'][target['cells'][0]['selector']];need(n['table_selector'] in target_ancestors and n['tbody_selector'] in target_ancestors,'business-source-neighbor-other-table');tr=_box(match['selected_raw_row_rect']);v=_box(match['selected_visible_cell_rect']);need(_inside(v,tr) and any(v==c['visible_box'] for p in proof['base_proof']['manual_local_previews'] if p['notice_id']==target['notice_id'] for c in p['cells']),'business-source-neighbor-target-rect-changed')
   overlap=min(r['right'],v['right'])>max(r['left'],v['left']) and min(r['bottom'],v['bottom'])>max(r['top'],v['top']);need(overlap and (rr['top']<tr['top']<rr['bottom']<tr['bottom'] and v['top']==tr['top'] if i<j else tr['top']<rr['top']<tr['bottom']<rr['bottom'] and v['bottom']==tr['bottom']),'business-source-neighbor-not-boundary-paint')
 return neighbors
