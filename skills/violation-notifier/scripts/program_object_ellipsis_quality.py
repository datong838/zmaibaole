"""Explicit object-only segment ellipsis contract. No capture or input."""
import copy,hashlib,json,math,re,subprocess,time
from pathlib import Path
import program_region_quality as full
need=full.need;document=full.document;data=full.data;ref=full.ref;compact=full.compact
METHOD=full.METHOD;FIELDS=full.FIELDS;HEADER=full.HEADER;date=full.date
KIND='violation-object-excerpt-program-quality-v1'
def walk(n):
 yield n
 for child in n.get('children',[]):yield from walk(child)
def one(xs,reason):need(len(xs)==1,reason);return xs[0]
def norm(s):return compact(s).replace('（','(').replace('）',')')
def leaves(n):return [x for x in walk(n)if x.get('name','').strip()and not any(z.get('name','').strip()for child in x.get('children',[])for z in walk(child))]
def segments(m,c):
 observation={'path':m['pinned_inputs']['observation_path'],'sha256':m['pinned_inputs']['observation_sha256']};tree=document(observation)['tree']['root'];node=one([n for n in walk(tree)if n.get('selector')==c['selector']],'excerpt-original-cell-selector');need(compact(node.get('name',''))==compact(c['text']),'excerpt-cell-source-conflict');parts=leaves(node)
 need(parts and compact(''.join(n['name']for n in parts))==compact(c['text']),'excerpt-complete-source-partition-required');allowed=set(c['text_selectors']);clips=c['geometry']['text_clips'];clipmap={x['selector']:x for x in clips};need(len(clipmap)==len(clips)and set(clipmap)<={n['selector']for n in parts},'excerpt-exact-clipped-leaf-required')
 for clip in clips:need(clip.get('supported')is True and clip.get('text_overflow')=='ellipsis'and clip.get('line_clamp')=='none'and clip.get('overflow_x')=='hidden'and clip.get('scroll_width',0)>clip.get('client_width',0)>0,'excerpt-unsupported-clip')
 result=[]
 for n in parts:
  selector=n['selector'];need(selector in allowed,'excerpt-leaf-not-source-diagnostic');cls=n.get('attributes',{}).get('class','');text=n['name'];anc=[a for a in walk(node)if selector.startswith(a['selector']+' > ')];classes={a.get('attributes',{}).get('class','')for a in anc};field=c['field'];role='core'
  if field=='reason':
   if 'punish_id_text-oFLFsi'in cls:role='identity_metadata'
   else:need('governance_merchant-tag'in cls or 'governance_merchant-typography-text'in cls,'excerpt-reason-leaf-unknown')
  elif field=='subject':
   if cls=='id-BAdXmN':role='identity_metadata'
   else:need('name-iUMfRa'in cls,'excerpt-subject-leaf-unknown')
  elif field=='object':
   if cls in('id_label-aOJH4P','id_label-hzjYGK')or classes.intersection({'id-xRLaKE','id-rYNLC7'}):role='identity_metadata'
   else:need(cls=='location-NKP7hj'or classes.intersection({'title-N634s8','title-r2FYfu','price-erFxLG'}),'excerpt-object-leaf-unknown')
  else:need(field in('effective_status','disposal')and cls.endswith('cell-body-xXyIpu'),'excerpt-state-leaf-unknown')
  need(selector not in clipmap or field=='object','excerpt-core-other-field-clipping-refused')
  result.append({'selector':selector,'text':text,'source_native_ellipsis':bool(re.search(r'…|\.\.\.',text)),'clipped':selector in clipmap,'role':role})
 need(any(x['role']=='core'for x in result),'excerpt-core-text-missing');return result
def plan(m):
 p=m['public_dom_proof']['before'];need(p==m['public_dom_proof']['after'],'quality-DOM-race');need(m['geometry_before']==m['geometry_after'],'quality-native-geometry-race')
 capture=document(m['capture_metadata']);need(capture['state']=='complete' and capture['capture_method']==METHOD,'quality-single-window-required')
 need(capture['before']['window']==capture['after']['window'] and capture['before']['scope']==capture['after']['scope'],'quality-window-race')
 need(capture['png']==m['derivation']['source'],'quality-capture-source-conflict')
 need(m['frame_mode']=='rows' and not m.get('capture_subcontract'),'quality-full-text-contract-required')
 base=p['base_proof'];selectors=p['selectors'];mapping=[]
 # Existing installed region-proof already binds its ordered selectedBounds in
 # static-decoration diagnostics. Reuse only exact, complete, consistent arrays.
 for a in p.get('unresolved_overlay',[])+p.get('preserved_translucent_backgrounds',[]):
  bounds=a.get('decoration_geometry',{}).get('selected_bounds')
  if bounds is not None:mapping.append(bounds)
 need(mapping and all(x==mapping[0] for x in mapping) and len(mapping[0])==len(selectors),'quality-existing-cell-rects-unavailable')
 bounds=mapping[0];need(len(set(selectors))==len(selectors),'quality-selector-duplicate')
 region=p['region'];need(all(abs(v-region[k])<1e-6 for k,v in [('left',min(b['left'] for b in bounds)),('top',min(b['top'] for b in bounds)),('right',max(b['right'] for b in bounds)),('bottom',max(b['bottom'] for b in bounds))]),'quality-rect-union-conflict')
 expected=[]
 if m['frame_mode']=='anchor':
  need([h['text']for h in base['business_headers']]==list(HEADER),'quality-five-header-contract')
  expected=[('date',base['business_date'])]+[(h['field'],h)for h in base['business_headers']]
  date(base['business_date']['text'])
 else:
  ids=m['notice_ids'];rows=[r for r in base['business_cells']if r['notice_id'] in ids];need(ids and [r['notice_id']for r in rows]==ids and len(ids)==len(set(ids)),'quality-exact-notices')
  for row in rows:
   need([c['field']for c in row['cells']]==list(FIELDS),'quality-five-source-fields')
   expected.extend((row['notice_id']+':'+c['field'],c)for c in row['cells'])
 g=m['geometry_before'];cg=g['CG_bounds'];area=g['AX']['AX_webarea'];v=p['viewport'];raw=m['derivation']['source'];crop=m['derivation']['crop_box_pixels'];image=m['image']
 sx=area['width']/v['width'];sy=area['height']/v['height'];px=raw['width']/cg['width'];py=raw['height']/cg['height'];need(v['visual_scale']==1 and abs(sx-sy)<=max(sx,sy)*.002 and abs(px-py)<=max(px,py)*.002,'quality-nonuniform-transform')
 cells=[]
 for key,c in expected:
  selector=c['selector'];need(selector in selectors,'quality-source-cell-not-selected');b=bounds[selectors.index(selector)];geo=c['geometry']
  partial=c['field']=='object' and geo.get('text_unclipped') is False
  need(all(geo.get(k)is True for k in ('rendered','box_viewport_contained','unsupported_css_absent','evidence_eligible')),'ellipsis-visible-cell-required')
  if partial: need(geo.get('ellipsis_supported') is True and geo.get('preview_required') is True and bool(geo.get('text_clips')),'ellipsis-explicit-supported-clipping-required')
  else: need(geo.get('text_unclipped') is True and not geo.get('text_clips'),'quality-full-cell-text-required')
  need(type(c['text'])is str and bool(c['text'].strip()),'quality-empty-cell-unsupported')
  vals=[b[k]for k in ('left','top','right','bottom')];need(all(type(x)in(int,float)and math.isfinite(x)for x in vals),'quality-finite-rect')
  l,t,r,d=vals;need(0<=l<r<=v['width']and 0<=t<d<=v['height'],'quality-cell-outside-viewport')
  box=[math.floor((area['x']-cg['x']+l*sx)*px)-crop[0],math.floor((area['y']-cg['y']+t*sy)*py)-crop[1],math.ceil((area['x']-cg['x']+r*sx)*px)-crop[0],math.ceil((area['y']-cg['y']+d*sy)*py)-crop[1]]
  need(0<=box[0]<box[2]<=image['width']and 0<=box[1]<box[3]<=image['height'],'quality-cell-outside-PNG')
  entry={'key':key,'selector':selector,'expected':c['text'],'box':box}
  entry['segments']=segments(m,c)
  cells.append(entry)
 need(any(p['clipped']for c in cells for p in c['segments']),'excerpt-explicit-object-clipping-required')
 return {'kind':'program-region-cell-plan-v1','image':image,'frame_mode':m['frame_mode'],'cells':cells,'source_sha256':m['source_sha256']}
def excerpt(part,text):
 source=norm(part['text']);seen=norm(text)
 if seen==source:return {'visible_excerpt':text,'source_prefix':source,'full_text_visible':True,'pixel_ellipsis_observed':bool(re.search(r'…|\.\.\.',seen)),'source_native_ellipsis':part['source_native_ellipsis']}
 need(part['clipped']and not part['source_native_ellipsis'],'excerpt-full-core-required')
 prefix=seen.rstrip('.…');suffix=seen[len(prefix):];need(len(prefix)>=8 and len(prefix)<len(source)and source.startswith(prefix),'excerpt-not-source-prefix')
 return {'visible_excerpt':text,'source_prefix':prefix,'full_text_visible':False,'pixel_ellipsis_observed':'…'in suffix or '...'in suffix,'source_native_ellipsis':False}

def groups(cell):
 core=[p for p in cell['segments']if p['role']=='core']
 if cell['key'].endswith(':object'):return [{'key':cell['key']+':core'+str(i),'parts':[p],'expected':p['text'],'clipped':p['clipped']}for i,p in enumerate(core)]
 return [{'key':cell['key']+':core','parts':core,'expected':' '.join(p['text']for p in core),'clipped':False}]

def locate(group,rows):
 expected=norm(group['expected']);found=[]
 def search(chain,text,start):
  good=False
  try:
   if group['clipped']:excerpt(group['parts'][0],text);good=True
   else:good=norm(text)==expected
  except ValueError:pass
  if good:found.append(chain);return
  if len(chain)>=12 or not expected.startswith(norm(text)):return
  for i in range(start,len(rows)):
   r=rows[i]
   if chain:
    last=chain[-1];needh=max(last['box'][3],r['box'][3]);lasttop=1-last['box'][1]-last['box'][3];top=1-r['box'][1]-r['box'][3]
    if top-lasttop>3*needh:continue
   search(chain+[r],text+r['text'],i+1)
 for i,r in enumerate(rows):search([r],r['text'],i+1)
 return one(found,'excerpt-locator-missing-or-ambiguous:'+group['key'])

def roi_plan(p,first):
 need(first.get('kind')=='local-vision-cell-ocr-v1'and first.get('recognition_level')=='accurate'and first.get('recognition_languages')==['zh-Hans','en-US']and first.get('language_correction')is False and first.get('CPU_only')is True,'excerpt-first-OCR-method');need(len(first['cells'])==len(p['cells']),'excerpt-first-cell-count');result=[]
 for cell,ocr in zip(p['cells'],first['cells']):
  need(ocr['key']==cell['key']and ocr['box']==cell['box'],'excerpt-first-cell-binding');rows=sorted(ocr['observations'],key=lambda r:(-round(r['box'][1]+r['box'][3]/2,2),r['box'][0]));cw,ch=cell['box'][2]-cell['box'][0],cell['box'][3]-cell['box'][1]
  for g in groups(cell):
   chain=locate(g,rows)
   for r in chain:need(len(r['box'])==4 and all(type(v)in(int,float)and math.isfinite(v)for v in r['box'])and r['box'][2]>0 and r['box'][3]>0,'excerpt-locator-finite-box')
   pad=max(2,math.ceil(max(r['box'][3]for r in chain)*ch*.3));box=[max(cell['box'][0],math.floor(cell['box'][0]+min(r['box'][0]for r in chain)*cw)-pad),max(cell['box'][1],math.floor(cell['box'][1]+min(1-r['box'][1]-r['box'][3]for r in chain)*ch)-pad),min(cell['box'][2],math.ceil(cell['box'][0]+max(r['box'][0]+r['box'][2]for r in chain)*cw)+pad),min(cell['box'][3],math.ceil(cell['box'][1]+max(1-r['box'][1]for r in chain)*ch)+pad)]
   need(0<=box[0]<box[2]<=p['image']['width']and 0<=box[1]<box[3]<=p['image']['height'],'excerpt-ROI-outside-original');result.append({**g,'cell_key':cell['key'],'box':box})
 return {'kind':'program-region-core-ROI-v1','image':p['image'],'cells':result,'derivation':'source-semantic-leaves-and-original-OCR-boxes','locator_is_not_quality_proof':True}

def reading_order(rows):
 # Font sizes in one semantic line may have different center-y; order shared
 # vertical bands from left to right before moving to the next line.
 pending=sorted(rows,key=lambda r:1-r['box'][1]-r['box'][3]);lines=[]
 for r in pending:
  top=1-r['box'][1]-r['box'][3];bottom=1-r['box'][1];matches=[]
  for line in lines:
   lt=max(1-x['box'][1]-x['box'][3]for x in line);lb=min(1-x['box'][1]for x in line)
   if min(bottom,lb)-max(top,lt)>=.5*min(r['box'][3],min(x['box'][3]for x in line)):matches.append(line)
  need(len(matches)<=1,'excerpt-reading-line-ambiguous')
  if matches:matches[0].append(r)
  else:lines.append([r])
 return [r for line in lines for r in sorted(line,key=lambda x:x['box'][0])]

def evaluate(p,ocr,roi):
 need(len(roi['cells'])==len(ocr['cells']),'excerpt-OCR-cell-count');checks=[]
 for g,o in zip(roi['cells'],ocr['cells']):
  ordered=reading_order(o['observations']);text=' '.join(r['text']for r in ordered)
  # Only OCR method/confidence/box validation uses the observed string. Source
  # equality/prefix below independently decides the finite business field.
  validation_text=' '.join(r['text']for r in sorted(o['observations'],key=lambda r:(-round(r['box'][1]+r['box'][3]/2,2),r['box'][0])))
  full.evaluate({'cells':[{**g,'expected':validation_text}]},{**ocr,'cells':[o]})
  if g['clipped']:result=excerpt(g['parts'][0],text)
  else:need(norm(text)==norm(g['expected']),'excerpt-full-core-mismatch:'+g['key']);result={'visible_excerpt':text,'full_text_visible':True,'pixel_ellipsis_observed':False}
  checks.append({'key':g['key'],'cell_key':g['cell_key'],'source_segments':g['parts'],'box':g['box'],**result})
 metadata=[{'cell_key':c['key'],'selector':part['selector'],'source_text_sha256':hashlib.sha256(part['text'].encode()).hexdigest(),'role':'identity_metadata','observed':False,'visible_excerpt':None,'full_text_visible':False}for c in p['cells']for part in c['segments']if part['role']=='identity_metadata']
 return {'kind':'source-bound-visible-excerpt-checks-v1','core':checks,'identity_metadata':metadata,'identity_metadata_observation_claimed':False,'cells':[{'key':c['key'],'business_core_verified':True,'full_cell_text_visibility_claimed':False,'source_identity_bound_by_original_validator':True}for c in p['cells']]}
def code_refs():return [ref(Path(__file__)),*full.code_refs()]
def verify(attestation,m,source):
 import region_frame_capture as region
 a=document(attestation);need(a.get('kind')==KIND and a.get('producer_method')=='local-Vision-source-bound-core-excerpts-v1'and a.get('decision')=='source-bound-visible-excerpts-verified'and 'reviewer_role'not in a,'excerpt-program-contract')
 preview=document(a['registration_preview']);expected=copy.deepcopy(m)
 for key in('quality_attestation','quality_approved_at'):expected.pop(key,None)
 expected['state']='awaiting-visual-review';need(preview==expected,'quality-original-preview-conflict');region.validate_frame(preview['image']['path'],preview,source=source,allow_preview=True)
 need(a['code']==code_refs()and a['binary']==full.runtime()and a['source']==source,'excerpt-program-pin-conflict')
 receipt=document(a['receipt']);p=plan(preview);roi=roi_plan(p,document(receipt['first_ocr']));need(receipt['kind']=='program-source-excerpt-receipt-v1'and receipt['preview']==a['registration_preview']and receipt['plan']==p and receipt['roi']==roi and receipt['binary']==a['binary']and receipt['code']==a['code']and receipt['cell_pixels']==full.pixel_refs(p),'excerpt-receipt-conflict')
 need(a['checks']==evaluate(p,document(receipt['ocr']),roi),'excerpt-checks-conflict');need(region.sr.when(preview['recorded_at'])<=region.sr.when(a['checked_at'])<=region.sr.when(m['quality_approved_at']),'quality-program-time')
 for r in(a['registration_preview'],a['receipt'],receipt['first_ocr'],receipt['ocr'],a['binary'],*a['code']):data(r)
 return a

def create(preview_ref,source,outdir):
 import region_frame_capture as region
 preview=document(preview_ref);need(preview.get('state')=='awaiting-visual-review','quality-original-preview-required');region.validate_frame(preview['image']['path'],preview,source=source,allow_preview=True)
 out=Path(outdir).resolve();final=out/'quality.json'
 if out.exists():
  need(final.exists(),'quality-existing-attempt-unresolved');verify(ref(final),{**preview,'state':'complete','quality_approved_at':region.stamp()},source);return ref(final)
 out.mkdir(parents=True);(out/'intent.json').write_text(json.dumps({'kind':'program-source-excerpt-intent-v1','preview':preview_ref,'source':source,'code':code_refs(),'started_at':region.stamp()}));start=time.monotonic()
 try:
  p=plan(preview);pixels=full.pixel_refs(p);(out/'plan.json').write_text(json.dumps(p,ensure_ascii=False));binary=full.runtime()
  for name,request in [('first-ocr',p),('ocr',None)]:
   if name=='ocr':request=roi_plan(p,document(ref(out/'first-ocr.json')))
   request_path=out/('plan.json'if name=='first-ocr'else'roi.json');request_path.write_text(json.dumps(request,ensure_ascii=False));run=subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',binary['path'],p['image']['path'],str(request_path)],capture_output=True,timeout=60);(out/(name+'.json')).write_bytes(run.stdout);(out/(name+'.stderr')).write_bytes(run.stderr);need(run.returncode==0,'quality-OCR-process-failed')
  roi=document(ref(out/'roi.json'));checks=evaluate(p,document(ref(out/'ocr.json')),roi);receipt={'kind':'program-source-excerpt-receipt-v1','preview':preview_ref,'plan':p,'roi':roi,'binary':binary,'code':code_refs(),'cell_pixels':pixels,'first_ocr':ref(out/'first-ocr.json'),'ocr':ref(out/'ocr.json'),'pipeline_elapsed_seconds':time.monotonic()-start};(out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False));region.validate_frame(preview['image']['path'],preview,source=source,allow_preview=True);data(preview_ref);data(p['image']);data(preview['derivation']['source']);data(binary)
  a={'kind':KIND,'producer_method':'local-Vision-source-bound-core-excerpts-v1','decision':'source-bound-visible-excerpts-verified','registration_preview':preview_ref,'source':source,'code':code_refs(),'binary':binary,'receipt':ref(out/'receipt.json'),'checks':checks,'checked_at':region.stamp()};final.write_text(json.dumps(a,ensure_ascii=False));return ref(final)
 except Exception as error:(out/'failure.json').write_text(json.dumps({'kind':'program-source-excerpt-exception-v1','preview':preview_ref,'reason':str(error),'elapsed_seconds':time.monotonic()-start}));raise

# W66 pure planning/evaluation draft. Not dispatched by verify/create and grants
# no approval. Pixel evidence production and independent verifier remain required.
PIXEL_EXCERPT_KIND='violation-five-field-pixel-leaf-excerpt-v1'
def pixel_leaf_contract(m):
 need(m.get('state')=='awaiting-visual-review' and m.get('frame_mode')=='rows' and not m.get('capture_subcontract'),'pixel-leaf-original-five-field-preview-required')
 before=m['public_dom_proof']['before'];base=before['base_proof'];ids=m['notice_ids'];rows=[r for r in base['business_cells']if r['notice_id']in ids]
 need(1<=len(ids)<=8 and len(set(ids))==len(ids) and [r['notice_id']for r in rows]==ids,'pixel-leaf-original-four-rows-required')
 observation={'path':m['pinned_inputs']['observation_path'],'sha256':m['pinned_inputs']['observation_sha256']};tree=document(observation)['tree']['root'];cells=[]
 for row in rows:
  need([c['field']for c in row['cells']]==list(FIELDS),'pixel-leaf-five-fields-required')
  for c in row['cells']:
   node=one([n for n in walk(tree)if n.get('selector')==c['selector']],'pixel-leaf-cell-selector')
   parts=leaves(node);need(parts and compact(''.join(p['name']for p in parts))==compact(c['text']),'pixel-leaf-source-partition')
   need(all(p['selector']in c['text_selectors']for p in parts),'pixel-leaf-source-selector')
   cells.append({'key':row['notice_id']+':'+c['field'],'field':c['field'],'selector':c['selector'],'source_text':c['text'],'leaves':[{'selector':p['selector'],'source_text':p['name']}for p in parts],'original_dom_geometry_claims':copy.deepcopy(c['geometry'])})
 return {'kind':'five-field-original-source-leaf-plan-v1','image':m['image'],'before':m['public_dom_proof']['before'],'after':m['public_dom_proof']['after'],'postguard_consistency':m.get('postguard_consistency'),'cells':cells,'original_proof_modified':False}

def evaluate_pixel_leaf_readings(plan,readings):
 """Semantic control only. A match does not authenticate pixel evidence."""
 need(readings.get('kind')=='five-field-independent-pixel-leaf-readings-v1'and readings.get('image')==plan['image'],'pixel-leaf-image-binding')
 need(len(readings.get('cells',[]))==len(plan['cells'])==20,'pixel-leaf-cell-count');results=[]
 for cell,seen in zip(plan['cells'],readings['cells']):
  need(seen.get('key')==cell['key'] and len(seen.get('leaves',[]))==len(cell['leaves']),'pixel-leaf-cell-binding')
  checked=[]
  for part,reading in zip(cell['leaves'],seen['leaves']):
   need(reading.get('selector')==part['selector'],'pixel-leaf-selector-binding')
   text=reading.get('visible_text');need(type(text)is str and bool(text.strip()),'pixel-leaf-visible-text-required')
   status=reading.get('visibility');need(status in('complete','ellipsis','clipped'),'pixel-leaf-status')
   if status=='complete':need(norm(text)==norm(part['source_text']),'pixel-leaf-full-text-mismatch')
   else:
    need(cell['field']=='object','pixel-leaf-other-field-incomplete')
    prefix=norm(text).rstrip('.…');need(len(prefix)>=2 and len(prefix)<len(norm(part['source_text'])) and norm(part['source_text']).startswith(prefix),'pixel-leaf-source-prefix')
    if status=='ellipsis':need(text.rstrip().endswith(('…','...')),'pixel-leaf-ellipsis-required')
   checked.append({'selector':part['selector'],'visible_text':text,'visibility':status,'full_text_visible':status=='complete'})
  complete=all(p['full_text_visible']for p in checked)
  if cell['field']=='object':need(not complete,'pixel-leaf-object-full-claim-refused')
  else:need(complete,'pixel-leaf-other-field-full-required')
  results.append({'key':cell['key'],'leaves':checked,'full_text_visible':complete,'visible_source_fragments':True})
 return {'kind':'five-field-pixel-leaf-semantic-checks-v1','cells':results,'all_five_fields_preserved':True,'pixel_evidence_authenticated':False,'approval_granted':False,'history_certified':False,'date_certified':False,'rows_semantics_certified':False}

PIXEL_REVIEW_REF={'path':str(Path(__file__).resolve().parents[3]/'work/2026-10-30/round009-issue66-original-waiting/ROOT-FIVE-FIELD-PIXEL-READINGS.json'),'sha256':'b894b8c786ab122312777518e307ee2875f95e4237f5d57e82f3cc09698741d1'}
def reviewed_pixel_facts(m,source,review_ref=None):
 """Current exact admission; pure reusable validation below grants no authority."""
 review_ref=PIXEL_REVIEW_REF if review_ref is None else review_ref
 need(review_ref==PIXEL_REVIEW_REF,'pixel-review-fixed-evidence-required')
 return independent_pixel_facts(m,source,review_ref)

def independent_pixel_facts(m,source,review_ref):
 """Pure five-field validation. Caller must separately admit exact review ref."""
 r=document(review_ref)
 need(r.get('kind')=='Root-saved-PNG-five-field-independent-pixel-readings-v1'and r.get('approved')is False and r.get('attestation_generated')is False and r.get('metadata_or_images_modified')is False,'pixel-review-observation-only')
 need(r['source']==source and r['image']==m['image'] and document(r['preview'])==m,'pixel-review-original-source-preview-image')
 need(all(r.get(k)is False for k in('history_resolved','date_certified','hidden_ID_suffixes_certified','per_glyph_coordinates_certified')) and r.get('original_DOM_claims_unchanged')is True and r.get('original_proof_is_not_independent_pixel_evidence')is True,'pixel-review-limits')
 p=pixel_leaf_contract(m);need([x['notice_id']for x in r['rows']]==m['notice_ids'],'pixel-review-exact-notices')
 checks=[]
 for row in r['rows']:
  need(set(row['fields'])==set(FIELDS),'pixel-review-five-fields')
  for field in FIELDS:
   c=one([c for c in p['cells']if c['key']==row['notice_id']+':'+field],'pixel-review-cell-unique');seen=row['fields'][field]
   need(seen.get('visible_fragment')is True and seen.get('full_text_visible')is(field!='object'),'pixel-review-cell-completeness')
   if field!='object':
    need(norm(seen['observed_text'])==norm(c['source_text']),'pixel-review-nonobject-full-text')
    leaves_checked=[];remaining=norm(seen['observed_text'])
    for leaf in c['leaves']:
     value=norm(leaf['source_text']);need(remaining.startswith(value),'pixel-review-nonobject-leaf-order');remaining=remaining[len(value):];leaves_checked.append({'selector':leaf['selector'],'visible_text':leaf['source_text'],'full_text_visible':True,'visibility':'complete'})
    need(not remaining,'pixel-review-nonobject-unassigned-text')
   else:
    readings=seen['leaf_readings'];need(len(readings)==len(c['leaves']),'pixel-review-object-all-leaves');leaves_checked=[]
    for leaf,reading in zip(c['leaves'],readings):
     text=reading['observed_text'];status=reading['visibility'];full_text=reading['full_text_visible'];need(type(text)is str and bool(text.strip()),'pixel-review-visible-leaf')
     if status=='complete':need(full_text is True and norm(text)==norm(leaf['source_text']),'pixel-review-object-complete-leaf')
     elif status=='ellipsis':need(full_text is False and 2<=len(norm(text))<len(norm(leaf['source_text']))and norm(leaf['source_text']).startswith(norm(text)),'pixel-review-object-exact-prefix')
     elif status=='clipped-not-complete-certified':need(full_text is False and norm(text)==norm(leaf['source_text']),'pixel-review-clipped-readable-not-certified')
     else:need(False,'pixel-review-unknown-visibility')
     leaves_checked.append({'selector':leaf['selector'],'visible_text':text,'full_text_visible':full_text,'visibility':status})
    need(any(x['full_text_visible']is False for x in leaves_checked),'pixel-review-object-full-forbidden')
   checks.append({'key':c['key'],'selector':c['selector'],'visible_fragment':True,'full_text_visible':field!='object','leaves':leaves_checked})
 # Hash exact pixels, without creating derivatives or asserting glyph geometry.
 data(r['image']);data(r['preview']);data(source)
 return {'kind':'verified-original-five-field-independent-pixel-facts-v1','review':review_ref,'preview':r['preview'],'source':source,'image':r['image'],'cells':checks,'all_five_fields_preserved':True,'original_DOM_claims':[{ 'key':c['key'],'geometry':c['original_dom_geometry_claims']}for c in p['cells']],'history_resolved':False,'date_certified':False,'hidden_ID_suffixes_certified':False,'per_glyph_coordinates_certified':False,'approval_performed':False}

def pixel_review_verify(attestation,m,source):
 import region_frame_capture as region
 a=document(attestation);need(a.get('kind')==PIXEL_EXCERPT_KIND and a.get('producer_method')=='fixed-reviewed-original-PNG-five-field-leaves-v1'and a.get('decision')=='five-field-visible-fragments-verified-history-unresolved'and 'reviewer_role'not in a,'pixel-review-attestation-contract')
 expected=copy.deepcopy(m)
 for key in('quality_attestation','quality_approved_at'):expected.pop(key,None)
 expected['state']='awaiting-visual-review';need(a.get('registration_preview')==document(PIXEL_REVIEW_REF)['preview']and document(a['registration_preview'])==expected,'pixel-review-original-preview')
 region.validate_frame(expected['image']['path'],expected,source=source,allow_preview=True)
 need(a.get('code')==code_refs() and a.get('review')==PIXEL_REVIEW_REF,'pixel-review-code-and-fixed-evidence')
 facts=reviewed_pixel_facts(expected,source,a['review']);need(a.get('pixel_facts')==facts,'pixel-review-derived-facts')
 need(region.sr.when(expected['recorded_at'])<=region.sr.when(document(PIXEL_REVIEW_REF)['reviewed_at'])<=region.sr.when(a['checked_at'])<=region.sr.when(m['quality_approved_at']),'pixel-review-time')
 need(a.get('history_resolved')is False and a.get('date_certified')is False and a.get('rows_semantics_certified')is False,'pixel-review-no-history-authority')
 return a
