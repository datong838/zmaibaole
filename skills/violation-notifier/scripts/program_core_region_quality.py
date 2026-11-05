"""Four business-core fields certified; object pixels retained, not certified."""
import copy,hashlib,json,math,subprocess,time
from pathlib import Path
import program_region_quality as full
import program_object_ellipsis_quality as excerpt
need=full.need;document=full.document;data=full.data;ref=full.ref;compact=full.compact
METHOD=full.METHOD;FIELDS=full.FIELDS;HEADER=full.HEADER;date=full.date
KIND='violation-four-core-region-program-quality-v1'
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
  entry['segments']=[] if c['field']=='object' else excerpt.segments(m,c)
  cells.append(entry)
 return {'kind':'program-region-cell-plan-v1','image':image,'frame_mode':m['frame_mode'],'cells':cells,'source_sha256':m['source_sha256']}
def required_roi(p,first):
 required=[c for c in p['cells']if not c['key'].endswith(':object')];keys={c['key']for c in required};need(len(first['cells'])==len(p['cells']),'core-first-cell-count')
 need([(x['key'],x['box'])for x in first['cells']]==[(c['key'],c['box'])for c in p['cells']],'core-first-cell-binding')
 return excerpt.roi_plan({**p,'cells':required},{**first,'cells':[c for c in first['cells']if c['key']in keys]})
def evaluate(p,first,second,roi):
 required=[c for c in p['cells']if not c['key'].endswith(':object')];v=excerpt.evaluate({**p,'cells':required},second,roi);need(len(v['core'])==len(required)and all(x['full_text_visible']is True for x in v['core']),'core-all-required-fields-complete')
 optional=[]
 for c,o in zip(p['cells'],first['cells']):
  if c['key'].endswith(':object'):
   optional.append({'key':c['key'],'selector':c['selector'],'source_text_sha256':hashlib.sha256(c['expected'].encode()).hexdigest(),'box':c['box'],'object_text_certified':False,'full_text_visible':False,'pixel_evidence_preserved':True,'observation_state':'unverified-local-OCR-observation','observations':copy.deepcopy(o['observations'])})
 return {'kind':'four-core-fields-with-object-pixels-v1','required_fields':['reason','subject','effective_status','disposal'],'required_core_checks':v['core'],'identity_metadata':v['identity_metadata'],'object_text_certified':False,'object_observations':optional,'all_fields_visible_claimed':False,'rectification_state_source_only':True}
def code_refs():return [ref(Path(__file__)),*excerpt.code_refs()]
def verify(attestation,m,source):
 import region_frame_capture as region
 a=document(attestation);need(a.get('kind')==KIND and a.get('producer_method')=='local-Vision-four-core-fields-object-pixels-v1'and a.get('decision')=='four-core-fields-verified-object-text-uncertified'and 'reviewer_role'not in a,'excerpt-program-contract')
 preview=document(a['registration_preview']);expected=copy.deepcopy(m)
 for key in('quality_attestation','quality_approved_at'):expected.pop(key,None)
 expected['state']='awaiting-visual-review';need(preview==expected,'quality-original-preview-conflict');region.validate_frame(preview['image']['path'],preview,source=source,allow_preview=True)
 need(a['code']==code_refs()and a['binary']==full.runtime()and a['source']==source,'excerpt-program-pin-conflict')
 receipt=document(a['receipt']);p=plan(preview);roi=required_roi(p,document(receipt['first_ocr']));need(receipt['kind']=='program-four-core-receipt-v1'and receipt['preview']==a['registration_preview']and receipt['plan']==p and receipt['roi']==roi and receipt['binary']==a['binary']and receipt['code']==a['code']and receipt['cell_pixels']==full.pixel_refs(p),'excerpt-receipt-conflict')
 need(a['checks']==evaluate(p,document(receipt['first_ocr']),document(receipt['ocr']),roi),'excerpt-checks-conflict');need(region.sr.when(preview['recorded_at'])<=region.sr.when(a['checked_at'])<=region.sr.when(m['quality_approved_at']),'quality-program-time')
 for r in(a['registration_preview'],a['receipt'],receipt['first_ocr'],receipt['ocr'],a['binary'],*a['code']):data(r)
 return a

def create(preview_ref,source,outdir):
 import region_frame_capture as region
 preview=document(preview_ref);need(preview.get('state')=='awaiting-visual-review','quality-original-preview-required');region.validate_frame(preview['image']['path'],preview,source=source,allow_preview=True)
 out=Path(outdir).resolve();final=out/'quality.json'
 if out.exists():
  need(final.exists(),'quality-existing-attempt-unresolved');verify(ref(final),{**preview,'state':'complete','quality_approved_at':region.stamp()},source);return ref(final)
 out.mkdir(parents=True);(out/'intent.json').write_text(json.dumps({'kind':'program-four-core-intent-v1','preview':preview_ref,'source':source,'code':code_refs(),'started_at':region.stamp()}));start=time.monotonic()
 try:
  p=plan(preview);pixels=full.pixel_refs(p);(out/'plan.json').write_text(json.dumps(p,ensure_ascii=False));binary=full.runtime()
  for name,request in [('first-ocr',p),('ocr',None)]:
   if name=='ocr':request=required_roi(p,document(ref(out/'first-ocr.json')))
   request_path=out/('plan.json'if name=='first-ocr'else'roi.json');request_path.write_text(json.dumps(request,ensure_ascii=False));run=subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',binary['path'],p['image']['path'],str(request_path)],capture_output=True,timeout=60);(out/(name+'.json')).write_bytes(run.stdout);(out/(name+'.stderr')).write_bytes(run.stderr);need(run.returncode==0,'quality-OCR-process-failed')
  roi=document(ref(out/'roi.json'));checks=evaluate(p,document(ref(out/'first-ocr.json')),document(ref(out/'ocr.json')),roi);receipt={'kind':'program-four-core-receipt-v1','preview':preview_ref,'plan':p,'roi':roi,'binary':binary,'code':code_refs(),'cell_pixels':pixels,'first_ocr':ref(out/'first-ocr.json'),'ocr':ref(out/'ocr.json'),'pipeline_elapsed_seconds':time.monotonic()-start};(out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False));region.validate_frame(preview['image']['path'],preview,source=source,allow_preview=True);data(preview_ref);data(p['image']);data(preview['derivation']['source']);data(binary)
  a={'kind':KIND,'producer_method':'local-Vision-four-core-fields-object-pixels-v1','decision':'four-core-fields-verified-object-text-uncertified','registration_preview':preview_ref,'source':source,'code':code_refs(),'binary':binary,'receipt':ref(out/'receipt.json'),'checks':checks,'checked_at':region.stamp()};final.write_text(json.dumps(a,ensure_ascii=False));return ref(final)
 except Exception as error:(out/'failure.json').write_text(json.dumps({'kind':'program-four-core-exception-v1','preview':preview_ref,'reason':str(error),'elapsed_seconds':time.monotonic()-start}));raise
