"""Finite local Vision region quality, distinct from supervisor attestation."""
import copy,datetime,hashlib,io,json,math,re,subprocess,sys,time
from pathlib import Path
from PIL import Image
METHOD='ScreenCaptureKit/SCScreenshotManager/desktopIndependentWindow'
FIELDS=('reason','subject','object','effective_status','disposal')
HEADER=('违规原因','处置主体','违规对象','处置生效状态','处置方式')
KIND='violation-frame-program-quality-v1'
RUNTIME_PIN={'binary_sha256': '1e3ea7643c47977c92cf66a71c0556b5e3522b65368de9dcaba2b0ab55894730', 'kind': 'local-region-quality-runtime-v1', 'swift_sha256': '84a6ff9f7512b2217c37eb0a7f5bd89637a130a1f54f44491bc7e177c624d2af'}
def need(ok,reason):
 if not ok:raise ValueError(reason)
def checksum(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ref(path):return {'path':str(Path(path).resolve()),'sha256':checksum(path)}
def data(r):
 p=Path(r['path']);need(p.is_absolute() and p.resolve()==p and not any(x.is_symlink() for x in (p,*p.parents)),'quality-canonical-path');b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==r['sha256'],'quality-reference-changed');return b
def document(r):return json.loads(data(r))
def compact(s):return ''.join(s.split())
def date(s):
 m=re.fullmatch(r'\s*(\d{4}/\d{2}/\d{2})\s*[~～]\s*(\d{4}/\d{2}/\d{2})\s*',s);need(m,'quality-full-date-required')
 d=tuple(datetime.datetime.strptime(x,'%Y/%m/%d').date() for x in m.groups());need(d[0]<=d[1],'quality-date-order');return d

def plan(m):
 p=m['public_dom_proof']['before'];need(p==m['public_dom_proof']['after'],'quality-DOM-race');need(m['geometry_before']==m['geometry_after'],'quality-native-geometry-race')
 capture=document(m['capture_metadata']);need(capture['state']=='complete' and capture['capture_method']==METHOD,'quality-single-window-required')
 need(capture['before']['window']==capture['after']['window'] and capture['before']['scope']==capture['after']['scope'],'quality-window-race')
 need(capture['png']==m['derivation']['source'],'quality-capture-source-conflict')
 need(m['frame_mode'] in ('anchor','rows') and not m.get('capture_subcontract'),'quality-full-text-contract-required')
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
  need(all(geo.get(k)is True for k in ('rendered','box_viewport_contained','unsupported_css_absent','text_unclipped','evidence_eligible')) and not geo.get('text_clips'),'quality-full-cell-text-required')
  need(type(c['text'])is str and bool(c['text'].strip()),'quality-empty-cell-unsupported')
  vals=[b[k]for k in ('left','top','right','bottom')];need(all(type(x)in(int,float)and math.isfinite(x)for x in vals),'quality-finite-rect')
  l,t,r,d=vals;need(0<=l<r<=v['width']and 0<=t<d<=v['height'],'quality-cell-outside-viewport')
  box=[math.floor((area['x']-cg['x']+l*sx)*px)-crop[0],math.floor((area['y']-cg['y']+t*sy)*py)-crop[1],math.ceil((area['x']-cg['x']+r*sx)*px)-crop[0],math.ceil((area['y']-cg['y']+d*sy)*py)-crop[1]]
  need(0<=box[0]<box[2]<=image['width']and 0<=box[1]<box[3]<=image['height'],'quality-cell-outside-PNG')
  cells.append({'key':key,'selector':selector,'expected':c['text'],'box':box})
 return {'kind':'program-region-cell-plan-v1','image':image,'frame_mode':m['frame_mode'],'cells':cells,'source_sha256':m['source_sha256']}

def pixel_refs(plan):
 image=data(plan['image']);out=[]
 with Image.open(io.BytesIO(image)) as im:
  im.load()
  for c in plan['cells']:out.append({'key':c['key'],'box':c['box'],'rgba_sha256':hashlib.sha256(im.crop(c['box']).convert('RGBA').tobytes()).hexdigest()})
 return out

def evaluate(plan,ocr):
 need(ocr.get('kind')=='local-vision-cell-ocr-v1' and ocr.get('recognition_level')=='accurate' and ocr.get('recognition_languages')==['zh-Hans','en-US'] and ocr.get('language_correction')is False and ocr.get('CPU_only')is True,'quality-OCR-contract')
 need(type(ocr.get('elapsed_seconds'))in(int,float) and math.isfinite(ocr['elapsed_seconds'])and ocr['elapsed_seconds']>=0,'quality-OCR-timing')
 need(len(ocr['cells'])==len(plan['cells']),'quality-OCR-cell-count');checks=[]
 for c,o in zip(plan['cells'],ocr['cells']):
  need(set(o)=={'key','box','observations'}and o['key']==c['key']and o['box']==c['box'],'quality-OCR-cell-binding');rows=o['observations'];need(rows,'quality-text-not-observed')
  for r in rows:
   need(set(r)=={'text','confidence','box'} and type(r['text'])is str and r['text'] and type(r['confidence'])in(int,float)and math.isfinite(r['confidence']) and .5<=r['confidence']<=1,'quality-OCR-uncertain')
   b=r['box'];need(len(b)==4 and all(type(x)in(int,float)and math.isfinite(x)for x in b)and b[2]>0 and b[3]>0,'quality-OCR-box')
   # Vision floating bounds may overshoot <=1px. Source DOM full-text geometry
   # plus the exact complete observed string, not this estimate, proves this field.
   w,h=c['box'][2]-c['box'][0],c['box'][3]-c['box'][1];need(b[0]>=-1/w and b[1]>=-1/h and b[0]+b[2]<=1+1/w and b[1]+b[3]<=1+1/h,'quality-OCR-box-outside-cell')
  # Vision returns line observations; source strings are whitespace-normalized.
  ordered=sorted(rows,key=lambda r:(-round(r['box'][1]+r['box'][3]/2,2),r['box'][0]));text=' '.join(r['text']for r in ordered)
  need(date(text)==date(c['expected'])if c['key']=='date'else compact(text)==compact(c['expected']),'quality-cell-text-mismatch:'+c['key'])
  checks.append({'key':c['key'],'expected_sha256':hashlib.sha256(c['expected'].encode()).hexdigest(),'observed_text':text})
 return checks

def runtime():
 manifest=Path(__file__).with_name('region-quality-runtime.json');value=document(ref(manifest));binary=Path(__file__).with_name('region-quality-ocr')
 need(value==RUNTIME_PIN and value=={'kind':'local-region-quality-runtime-v1','swift_sha256':checksum(Path(__file__).with_name('region-quality-ocr.swift')),'binary_sha256':checksum(binary)},'quality-runtime-pin-changed');return ref(binary)

def code_refs():
 return [ref(Path(__file__)),ref(Path(__file__).with_name('region-quality-ocr.swift')),ref(Path(__file__).with_name('region-quality-runtime.json'))]

def verify(attestation,m,source):
 import region_frame_capture as region
 a=document(attestation);need(a.get('kind')==KIND and a.get('producer_method')=='local-Vision-exact-source-cells-v1' and 'reviewer_role'not in a and a.get('decision')=='finite-fields-verified','quality-program-contract')
 preview=document(a['registration_preview']);expected=copy.deepcopy(m)
 for key in ('quality_attestation','quality_approved_at'):expected.pop(key,None)
 expected['state']='awaiting-visual-review';need(preview==expected,'quality-original-preview-conflict')
 # No completed metadata is allowed to recursively bless itself.
 region.validate_frame(preview['image']['path'],preview,source=source,allow_preview=True)
 need(a['code']==code_refs(),'quality-program-code-changed');need(a['binary']==runtime(),'quality-program-binary-changed');need(a['source']==source,'quality-program-source-binding')
 receipt=document(a['receipt']);plan0=plan(preview);ocr=document(receipt['ocr'])
 need(receipt['kind']=='program-region-ocr-receipt-v1' and receipt['preview']==a['registration_preview']and receipt['plan']==plan0 and receipt['binary']==a['binary']and receipt['code']==a['code']and receipt['cell_pixels']==pixel_refs(plan0),'quality-program-receipt-binding')
 checks=evaluate(plan0,ocr);need(a['checks']==checks,'quality-program-checks-changed');need(region.sr.when(preview['recorded_at'])<=region.sr.when(a['checked_at'])<=region.sr.when(m['quality_approved_at']),'quality-program-time')
 for r in (a['registration_preview'],a['receipt'],receipt['ocr'],a['binary'],*a['code']):data(r)
 return a

def create(preview_ref,source,outdir):
 """Automatic finite producer. No bridge/native capture/approval call."""
 import region_frame_capture as region
 preview=document(preview_ref);need(preview.get('state')=='awaiting-visual-review','quality-original-preview-required')
 if preview.get('frame_mode')=='rows'and any(c.get('field')=='object'and c.get('geometry',{}).get('text_unclipped')is False for row in preview['public_dom_proof']['before']['base_proof'].get('business_cells',[])if row['notice_id']in preview.get('notice_ids',[])for c in row['cells']):
  import program_core_region_quality as core
  return core.create(preview_ref,source,outdir)
 region.validate_frame(preview['image']['path'],preview,source=source,allow_preview=True)
 out=Path(outdir).resolve();final=out/'quality.json'
 if out.exists():
  need(final.exists(),'quality-existing-attempt-unresolved')
  completed={**preview,'state':'complete','quality_approved_at':region.stamp()};verify(ref(final),completed,source);return ref(final)
 out.mkdir(parents=True);intent={'kind':'program-region-quality-intent-v1','preview':preview_ref,'source':source,'code':code_refs(),'started_at':region.stamp()};(out/'intent.json').write_text(json.dumps(intent))
 start=time.monotonic()
 try:
  p=plan(preview);pixels=pixel_refs(p);(out/'plan.json').write_text(json.dumps(p,ensure_ascii=False))
  br=runtime();run=subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',br['path'],p['image']['path'],str(out/'plan.json')],capture_output=True,timeout=60)
  (out/'ocr.json').write_bytes(run.stdout);(out/'ocr.stderr').write_bytes(run.stderr);need(run.returncode==0,'quality-OCR-process-failed');ocr=document(ref(out/'ocr.json'));checks=evaluate(p,ocr)
  receipt={'kind':'program-region-ocr-receipt-v1','preview':preview_ref,'plan':p,'binary':br,'code':code_refs(),'cell_pixels':pixels,'ocr':ref(out/'ocr.json'),'pipeline_elapsed_seconds':time.monotonic()-start};(out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False))
  a={'kind':KIND,'producer_method':'local-Vision-exact-source-cells-v1','decision':'finite-fields-verified','registration_preview':preview_ref,'source':source,'code':code_refs(),'binary':br,'receipt':ref(out/'receipt.json'),'checks':checks,'checked_at':region.stamp()}
  # Full chain and all inputs are checked again before artifact publication.
  region.validate_frame(preview['image']['path'],preview,source=source,allow_preview=True)
  data(preview_ref);data(p['image']);data(preview['derivation']['source']);data(br)
  final.write_text(json.dumps(a,ensure_ascii=False));return ref(final)
 except Exception as error:
  (out/'failure.json').write_text(json.dumps({'kind':'program-region-quality-exception-v1','preview':preview_ref,'source':source,'reason':str(error),'elapsed_seconds':time.monotonic()-start}));raise


FRAGMENT_KIND="violation-anchor-date-fragment-program-quality-v1"
FRAGMENT_CAPTION="截图日期控件仅显示片段，不认证图内完整日期；完整日期以已核验DOM查询与源表格为准。"
def fragment_date_geometry(base):
 d=base.get('business_date',{});g=d.get('geometry',{});clips=g.get('text_clips',[])
 if not (g.get('rendered') is True and g.get('box_viewport_contained') is True and g.get('unsupported_css_absent') is True and g.get('text_unclipped') is False and g.get('evidence_eligible') is False and len(clips)==1):return False
 c=clips[0]
 return c.get('selector')==d.get('selector') and c.get('supported') is False and c.get('text_overflow')=='clip' and c.get('line_clamp')=='none' and c.get('overflow_x')==c.get('overflow_y')=='clip' and all(type(c.get(k)) in (int,float) and math.isfinite(c[k]) and c[k]>0 for k in ('client_width','client_height','scroll_width','scroll_height')) and c['scroll_width']>c['client_width'] and c['scroll_height']==c['client_height']


def fragment_plan(m,source):
 import region_frame_capture as region
 p=m['public_dom_proof']['before'];need(p==m['public_dom_proof']['after'] and m['geometry_before']==m['geometry_after'] and not m.get('postguard_consistency'),'fragment-quality-postguard-exact-required')
 inputs=region.metadata_inputs(m);need(inputs.get('screenshot_anchor') is not None and source=={'path':m['pinned_inputs']['source_path'],'sha256':m['pinned_inputs']['source_sha256']},'fragment-quality-source-identity-binding')
 need(m['frame_mode']=='anchor' and m.get('capture_subcontract')==region.business.LOCAL and m.get('date_visible_fragment_in_image') is True and m.get('date_filter_visible') is False and m.get('date_text_complete_in_image') is False and m.get('list_headers_visible') is True,'fragment-quality-explicit-contract-required')
 base=p['base_proof'];need(region.business.manual_date_fragment(base),'fragment-quality-observed-date-clip-required');need([h['text']for h in base['business_headers']]==list(HEADER) and all(h['geometry']['evidence_eligible'] is True and h['geometry']['text_unclipped'] is True for h in base['business_headers']),'fragment-quality-five-headers')
 need(p['selectors']==[base['business_date']['selector'],*[h['selector'] for h in base['business_headers']]] and len(set(p['selectors']))==6,'fragment-quality-six-exact-selectors')
 dates=date(base['business_date']['text']);src=document(source);need(dates==(datetime.date.fromisoformat(src['start']),datetime.date.fromisoformat(src['end_exclusive'])-datetime.timedelta(days=1)),'fragment-quality-source-date-conflict')
 capture=document(m['capture_metadata']);need(capture['state']=='complete' and capture['capture_method']==METHOD and capture['before']['window']==capture['after']['window'] and capture['before']['scope']==capture['after']['scope'] and capture['png']==m['derivation']['source'],'fragment-quality-native-capture-binding')
 fragment={'caption':FRAGMENT_CAPTION,'full_date_visible':False,'full_date_certified':False,'date_control_pixels_preserved':True,'full_date_source':'pinned-DOM-query-and-source-records','source_value':base['business_date']['text'],'selector':base['business_date']['selector'],'source_sha256':source['sha256'],'profile_sha256':m['pinned_inputs']['profile_sha256'],'screenshot_anchor':m['pinned_inputs']['screenshot_anchor']}
 image=m['image'];need(type(image['width']) is int and type(image['height']) is int and image['width']>0 and image['height']>0,'fragment-quality-image-size');return {'kind':'program-anchor-whole-region-ocr-plan-v1','image':image,'frame_mode':'anchor','cells':[{'key':'six-selector-anchor-region','box':[0,0,image['width'],image['height']]}],'source_sha256':source['sha256'],'header_literals':list(HEADER),'date_fragment':fragment,'per_selector_OCR_geometry_claimed':False}

def fragment_evaluate(plan,ocr):
 need(ocr.get('kind')=='local-vision-cell-ocr-v1' and ocr.get('recognition_level')=='accurate' and ocr.get('recognition_languages')==['zh-Hans','en-US'] and ocr.get('language_correction') is False and ocr.get('CPU_only') is True,'quality-OCR-contract');need(type(ocr.get('elapsed_seconds')) in (int,float) and math.isfinite(ocr['elapsed_seconds']) and ocr['elapsed_seconds']>=0,'quality-OCR-timing');need(len(ocr.get('cells',[]))==1,'fragment-quality-OCR-cell-count');cell=ocr['cells'][0];want=plan['cells'][0];need(set(cell)=={'key','box','observations'} and cell['key']==want['key'] and cell['box']==want['box'],'quality-OCR-cell-binding');rows=cell['observations'];need(isinstance(rows,list) and 5<=len(rows)<=100,'fragment-quality-observations');selected=[]
 for label in HEADER:
  matches=[r for r in rows if isinstance(r,dict) and compact(r.get('text',''))==compact(label)];need(len(matches)==1,'fragment-quality-header-not-unique:'+label);row=matches[0];need(set(row)=={'text','confidence','box'} and type(row['confidence']) in (int,float) and math.isfinite(row['confidence']) and .5<=row['confidence']<=1,'quality-OCR-uncertain');b=row['box'];need(isinstance(b,list) and len(b)==4 and all(type(x) in (int,float) and math.isfinite(x) for x in b) and b[2]>0 and b[3]>0 and b[0]>=0 and b[1]>=0 and b[0]+b[2]<=1 and b[1]+b[3]<=1,'fragment-quality-header-outside-image');selected.append(row)
 need(max(r['box'][1] for r in selected)<min(r['box'][1]+r['box'][3] for r in selected) and all(a['box'][0]+a['box'][2]<=b['box'][0] for a,b in zip(selected,selected[1:])),'fragment-quality-header-order-baseline')
 return {'header_checks':[{'header':label,'observed_text':row['text'],'confidence':row['confidence'],'whole_region_normalized_box':row['box']} for label,row in zip(HEADER,selected)],'unverified_other_OCR_observations':[copy.deepcopy(row) for row in rows if row not in selected],'full_date_visible':False,'full_date_certified':False,'per_selector_OCR_geometry_claimed':False}

def fragment_source_binding(original,current):
 need(set(original)==set(current)=={'path','sha256'} and original['sha256']==current['sha256'] and data(original)==data(current),'fragment-quality-source-bytes-changed')


def fragment_verify(attestation,m,source):
 import region_frame_capture as region
 a=document(attestation);need(a.get('kind')==FRAGMENT_KIND and a.get('producer_method')=='local-Vision-five-headers-date-fragment-v1' and a.get('decision')=='five-headers-verified-date-fragment-uncertified' and 'reviewer_role' not in a,'fragment-quality-program-contract')
 preview=document(a['registration_preview']);expected=copy.deepcopy(m)
 for key in ('quality_attestation','quality_approved_at'):expected.pop(key,None)
 expected['state']='awaiting-visual-review';need(preview==expected,'quality-original-preview-conflict');region.validate_frame(preview['image']['path'],preview,source=source,allow_preview=True)
 need(a['code']==code_refs() and a['binary']==runtime(),'quality-program-pin-conflict');fragment_source_binding(a['source'],source);receipt=document(a['receipt']);p=fragment_plan(preview,a['source'])
 need(receipt['kind']=='program-anchor-date-fragment-receipt-v1' and receipt['preview']==a['registration_preview'] and receipt['plan']==p and receipt['binary']==a['binary'] and receipt['code']==a['code'] and receipt['cell_pixels']==pixel_refs(p),'fragment-quality-receipt-conflict')
 need(a['checks']==fragment_evaluate(p,document(receipt['ocr'])) and a.get('date_fragment')==p['date_fragment'] and a.get('caption')==FRAGMENT_CAPTION,'fragment-quality-checks-conflict');need(region.sr.when(preview['recorded_at'])<=region.sr.when(a['checked_at'])<=region.sr.when(m['quality_approved_at']),'quality-program-time')
 for r in (a['registration_preview'],a['receipt'],receipt['ocr'],a['binary'],*a['code']):data(r)
 return a

def fragment_create(preview_ref,source,outdir):
 import region_frame_capture as region
 if document(preview_ref).get('postguard_consistency') is not None:return epoch_fragment_create(preview_ref,source,outdir)
 preview=document(preview_ref);need(preview.get('state')=='awaiting-visual-review','quality-original-preview-required');region.validate_frame(preview['image']['path'],preview,source=source,allow_preview=True)
 out=Path(outdir).resolve();final=out/'quality.json'
 if out.exists():
  need(final.exists(),'quality-existing-attempt-unresolved');fragment_verify(ref(final),{**preview,'state':'complete','quality_approved_at':region.stamp()},source);return ref(final)
 out.mkdir(parents=True);(out/'intent.json').write_text(json.dumps({'kind':'program-anchor-date-fragment-intent-v1','preview':preview_ref,'source':source,'code':code_refs(),'started_at':region.stamp()}));start=time.monotonic()
 try:
  p=fragment_plan(preview,source);pixels=pixel_refs(p);(out/'plan.json').write_text(json.dumps(p,ensure_ascii=False));binary=runtime();run=subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',binary['path'],p['image']['path'],str(out/'plan.json')],capture_output=True,timeout=60);(out/'ocr.json').write_bytes(run.stdout);(out/'ocr.stderr').write_bytes(run.stderr);need(run.returncode==0,'quality-OCR-process-failed');checks=fragment_evaluate(p,document(ref(out/'ocr.json')))
  receipt={'kind':'program-anchor-date-fragment-receipt-v1','preview':preview_ref,'plan':p,'binary':binary,'code':code_refs(),'cell_pixels':pixels,'ocr':ref(out/'ocr.json'),'pipeline_elapsed_seconds':time.monotonic()-start};(out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False));region.validate_frame(preview['image']['path'],preview,source=source,allow_preview=True);data(preview_ref);data(p['image']);data(preview['derivation']['source']);data(binary)
  a={'kind':FRAGMENT_KIND,'producer_method':'local-Vision-five-headers-date-fragment-v1','decision':'five-headers-verified-date-fragment-uncertified','registration_preview':preview_ref,'source':source,'code':code_refs(),'binary':binary,'receipt':ref(out/'receipt.json'),'checks':checks,'date_fragment':p['date_fragment'],'caption':FRAGMENT_CAPTION,'checked_at':region.stamp()};final.write_text(json.dumps(a,ensure_ascii=False));return ref(final)
 except Exception as error:(out/'failure.json').write_text(json.dumps({'kind':'program-anchor-date-fragment-exception-v1','preview':preview_ref,'source':source,'reason':str(error),'elapsed_seconds':time.monotonic()-start}));raise


EPOCH_FRAGMENT_KIND='violation-anchor-five-header-pixel-quality-epoch-unresolved-v1'
EPOCH_FRAGMENT_CAPTION=FRAGMENT_CAPTION+' 全局DOM epoch变化原因未证实；仅认证本PNG五列表头像素，不认证变化历史或数据行。'
def epoch_fragment_plan(m,source):
 """Pixel-only sub-contract; original unresolved history is never rewritten."""
 import region_frame_capture as region
 need(m.get('frame_mode')=='anchor' and m.get('notice_ids')==[],'epoch-header-anchor-empty-notices-required')
 consistency=region.postguard.verify_pair(m,business=True)
 need(consistency is not None and consistency.get('contract')=='unresolved-global-epoch-change-v1' and consistency.get('automatic_certification') is False and consistency.get('semantic_or_layout_history_resolved') is False and consistency.get('outside_scope_cause_proven') is False,'epoch-header-original-unresolved-required')
 # Equality apart from the monotonically increasing epoch was checked above.
 # A normalized COPY is used solely to reuse existing field/ROI planning;
 # original full validate_frame, receipts, owner audit and proof remain intact.
 layout=copy.deepcopy(m);layout['public_dom_proof']['after']=copy.deepcopy(layout['public_dom_proof']['before']);layout.pop('postguard_consistency')
 p=fragment_plan(layout,source)
 return {**p,'kind':'program-anchor-five-header-pixel-plan-epoch-unresolved-v1','postguard_consistency':copy.deepcopy(consistency),'history_resolved':False,'automatic_history_certification':False,'row_fields_certified':False,'certified_pixels':'five-header-literals-only','caption':EPOCH_FRAGMENT_CAPTION}

def epoch_fragment_verify(attestation,m,source):
 import region_frame_capture as region
 a=document(attestation);need(a.get('kind')==EPOCH_FRAGMENT_KIND and a.get('producer_method')=='local-Vision-five-header-pixels-unresolved-epoch-v1' and a.get('decision')=='five-header-pixels-verified-history-unresolved' and 'reviewer_role' not in a,'fragment-quality-program-contract')
 need(a.get('history_resolved') is False and a.get('row_fields_certified') is False and a.get('automatic_history_certification') is False,'epoch-header-no-history-or-rows-certification')
 preview=document(a['registration_preview']);expected=copy.deepcopy(m)
 for key in ('quality_attestation','quality_approved_at'):expected.pop(key,None)
 expected['state']='awaiting-visual-review';need(preview==expected,'quality-original-preview-conflict');region.validate_frame(preview['image']['path'],preview,source=source,allow_preview=True)
 need(a['code']==code_refs() and a['binary']==runtime(),'quality-program-pin-conflict');fragment_source_binding(a['source'],source);receipt=document(a['receipt']);p=epoch_fragment_plan(preview,a['source'])
 need(receipt['kind']=='program-anchor-epoch-unresolved-pixel-receipt-v1' and receipt['preview']==a['registration_preview'] and receipt['plan']==p and receipt['binary']==a['binary'] and receipt['code']==a['code'] and receipt['cell_pixels']==pixel_refs(p),'fragment-quality-receipt-conflict')
 need(a['checks']==epoch_header_checks(p,document(receipt['ocr']),receipt.get('fallback')) and a.get('date_fragment')==p['date_fragment'] and a.get('caption')==EPOCH_FRAGMENT_CAPTION,'fragment-quality-checks-conflict');need(region.sr.when(preview['recorded_at'])<=region.sr.when(a['checked_at'])<=region.sr.when(m['quality_approved_at']),'quality-program-time')
 if receipt.get('cached_release') is None:
  stages=receipt.get('stage_execution',{});need(set(stages)==({'ocr','locator','second'}if receipt.get('fallback')else{'ocr'}),'epoch-header-stage-exit-closure');verify_epoch_stage_exit(stages['ocr'],a['binary'],receipt['ocr'])
  if receipt.get('fallback'):
   fb=receipt['fallback'];verify_epoch_stage_exit(stages['locator'],fb['locator_runtime']['binary'],fb['locator']);verify_epoch_stage_exit(stages['second'],a['binary'],fb['second'])
 if receipt.get('cached_release') is not None:
  need(receipt.get('stage_execution')=={},'epoch-header-cache-no-new-stage-exits')
  evidence=cached_header_evidence(receipt['cached_release'],a['registration_preview'],a['source'],p);need(evidence['first']==receipt['ocr'] and all(evidence[k]==receipt['fallback'][k]for k in ('locator','locator_stderr','second','second_stderr','locator_runtime')),'epoch-header-cache-receipt-binding')
 for r in (a['registration_preview'],a['receipt'],receipt['ocr'],a['binary'],*a['code']):data(r)
 return a

def epoch_fragment_create(preview_ref,source,outdir,*,cached_release=None):
 import region_frame_capture as region
 preview=document(preview_ref);need(preview.get('state')=='awaiting-visual-review','quality-original-preview-required');p=epoch_fragment_plan(preview,source);region.validate_frame(preview['image']['path'],preview,source=source,allow_preview=True)
 out=Path(outdir).resolve();final=out/'quality.json'
 if out.exists():
  need(final.exists(),'quality-existing-attempt-unresolved');epoch_fragment_verify(ref(final),{**preview,'state':'complete','quality_approved_at':region.stamp()},source);return ref(final)
 out.mkdir(parents=True);(out/'intent.json').write_text(json.dumps({'kind':'program-anchor-epoch-unresolved-pixel-intent-v1','preview':preview_ref,'source':source,'code':code_refs(),'cached_release':cached_release,'started_at':region.stamp()}));start=time.monotonic()
 def publish(name,value):path=out/name;path.write_text(json.dumps(value,ensure_ascii=False));return ref(path)
 stage_execution={}
 def once(name,value):
  path=out/name;raw=json.dumps(value,ensure_ascii=False).encode()
  with path.open('xb')as stream:stream.write(raw)
  return ref(path)
 def run(binary,plan,name):
  planref=publish(name+'-plan.json',plan);argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',binary['path'],p['image']['path'],planref['path']];started=time.monotonic();intent={'kind':'epoch-header-OCR-dispatch-intent-v1','stage':name,'argv':argv,'binary':binary,'plan':planref,'started_at':region.stamp(),'started_monotonic':started,'PID_available':False};dispatch=once(name+'-dispatch.json',intent)
  try:r=subprocess.run(argv,capture_output=True,timeout=60)
  except subprocess.TimeoutExpired as error:
   (out/(name+'.json')).write_bytes(error.stdout or b'');(out/(name+'.stderr')).write_bytes(error.stderr or b'');once(name+'-timeout.json',{'kind':'epoch-header-OCR-timeout-unknown-v1','dispatch':dispatch,'stdout':ref(out/(name+'.json')),'stderr':ref(out/(name+'.stderr')),'observed_at':region.stamp(),'elapsed_seconds':time.monotonic()-started,'natural_returncode_available':False});raise
  (out/(name+'.json')).write_bytes(r.stdout);(out/(name+'.stderr')).write_bytes(r.stderr);ended=time.monotonic();exitref=once(name+'-exit.json',{'kind':'epoch-header-OCR-natural-exit-v1','dispatch':dispatch,'stage':name,'argv':argv,'binary':binary,'plan':planref,'stdout':ref(out/(name+'.json')),'stderr':ref(out/(name+'.stderr')),'returncode':r.returncode,'started_at':intent['started_at'],'exited_at':region.stamp(),'started_monotonic':started,'exited_monotonic':ended,'elapsed_seconds':ended-started,'PID_available':False});stage_execution[name]=exitref;need(r.returncode==0,'epoch-header-'+name+'-OCR-nonzero');return ref(out/(name+'.json')),ref(out/(name+'.stderr')),planref

 try:
  pixels=pixel_refs(p);publish('plan.json',p);binary=runtime();fallback=None
  if cached_release is not None:
   evidence=cached_header_evidence(cached_release,preview_ref,source,p);ocrref=evidence['first'];lp=evidence['locator_plan_value'];roi=evidence['ROI_value'];fallback={k:evidence[k]for k in ('locator_runtime','locator','locator_stderr','second','second_stderr')};fallback.update(locator_plan=publish('locator-plan.json',lp),second_plan=publish('second-plan.json',roi),ROI_pixels=pixel_refs(roi),locator_returncode=0,second_returncode=0)
  else:
   ocrref,stderr,_=run(binary,p,'ocr');first=document(ocrref)
   try:fragment_evaluate(p,first)
   except ValueError:
    lp=header_fallback_plan(p,first);lr=locator_runtime();locator,le,lplan=run(lr['binary'],lp,'locator');roi=header_fallback_ROI(p,first,document(locator));second,se,splan=run(binary,roi,'second');fallback={'locator_runtime':lr,'locator_plan':lplan,'locator':locator,'locator_stderr':le,'second_plan':splan,'second':second,'second_stderr':se,'ROI_pixels':pixel_refs(roi),'locator_returncode':0,'second_returncode':0}
  checks=epoch_header_checks(p,document(ocrref),fallback);receipt={'kind':'program-anchor-epoch-unresolved-pixel-receipt-v1','preview':preview_ref,'plan':p,'binary':binary,'code':code_refs(),'cell_pixels':pixels,'ocr':ocrref,'stage_execution':stage_execution,'pipeline_elapsed_seconds':time.monotonic()-start,**({'fallback':fallback}if fallback else {}),**({'cached_release':cached_release}if cached_release else {})};receiptref=publish('receipt.json',receipt);region.validate_frame(preview['image']['path'],preview,source=source,allow_preview=True);data(preview_ref);data(p['image']);data(preview['derivation']['source']);data(binary)
  a={'kind':EPOCH_FRAGMENT_KIND,'history_resolved':False,'row_fields_certified':False,'automatic_history_certification':False,'producer_method':'local-Vision-five-header-pixels-unresolved-epoch-v1','decision':'five-header-pixels-verified-history-unresolved','registration_preview':preview_ref,'source':source,'code':code_refs(),'binary':binary,'receipt':receiptref,'checks':checks,'date_fragment':p['date_fragment'],'caption':EPOCH_FRAGMENT_CAPTION,'checked_at':region.stamp()};final.write_text(json.dumps(a,ensure_ascii=False));return ref(final)
 except Exception as error:publish('failure.json',{'kind':'program-anchor-epoch-unresolved-pixel-exception-v1','preview':preview_ref,'source':source,'reason':str(error),'elapsed_seconds':time.monotonic()-start});raise

LOCATOR_RUNTIME_PIN={'kind':'local-review-quality-runtime-v1','swift_sha256':'9ab7203779cb871e83453987d93a1811bc59ae80dda417655c53b9bc4858faa8','binary_sha256':'ca497b0f4e5e4b90d08db990e0af96a736049369175cd6fbeacf24fa35df800d'}
def locator_runtime():
 folder=Path(__file__).resolve().parents[2]/'negative-review-complaints/scripts';manifest=ref(folder/'review-quality-runtime.json');swift=ref(folder/'review-quality-ocr.swift');binary=ref(folder/'review-quality-ocr')
 need(document(manifest)==LOCATOR_RUNTIME_PIN and swift['sha256']==LOCATOR_RUNTIME_PIN['swift_sha256'] and binary['sha256']==LOCATOR_RUNTIME_PIN['binary_sha256'],'epoch-header-locator-runtime-pin')
 return {'manifest':manifest,'swift':swift,'binary':binary}
def _header_method(ocr):
 need(ocr.get('kind')=='local-vision-cell-ocr-v1' and ocr.get('recognition_level')=='accurate' and ocr.get('recognition_languages')==['zh-Hans','en-US'] and ocr.get('language_correction')is False and ocr.get('CPU_only')is True,'quality-OCR-contract')
 need(type(ocr.get('elapsed_seconds'))in(int,float) and math.isfinite(ocr['elapsed_seconds'])and ocr['elapsed_seconds']>=0,'quality-OCR-timing')
def _header_bounds(b,w,h,tolerance=0):
 need(isinstance(b,list) and len(b)==4 and all(type(x)in(int,float)and math.isfinite(x)for x in b)and b[2]>0 and b[3]>0 and b[0]>=-tolerance/w and b[1]>=-tolerance/h and b[0]+b[2]<=1+tolerance/w and b[1]+b[3]<=1+tolerance/h,'epoch-header-bounds')
def _header_order(rows):
 need(max(r['box'][1]for r in rows)<min(r['box'][1]+r['box'][3]for r in rows) and all(a['box'][0]+a['box'][2]<=b['box'][0]for a,b in zip(rows,rows[1:])),'fragment-quality-header-order-baseline')
def header_fallback_plan(p,first):
 _header_method(first);need(len(first.get('cells',[]))==1,'epoch-header-first-cell-count');cell=first['cells'][0];want=p['cells'][0];need(set(cell)=={'key','box','observations'}and cell['key']==want['key']and cell['box']==want['box'],'quality-OCR-cell-binding');rows=cell['observations'];need(type(rows)is list and 5<=len(rows)<=100,'fragment-quality-observations');good={};failed=[];w,h=p['image']['width'],p['image']['height']
 for index,label in enumerate(HEADER):
  hits=[(i,r)for i,r in enumerate(rows)if isinstance(r,dict)and compact(r.get('text',''))==compact(label)]
  try:
   need(len(hits)==1,'epoch-header-first-not-unique');i,r=hits[0];need(set(r)=={'text','confidence','box'}and type(r['confidence'])in(int,float)and math.isfinite(r['confidence'])and .5<=r['confidence']<=1,'quality-OCR-uncertain');_header_bounds(r['box'],w,h);good[index]={'index':i,**copy.deepcopy(r)}
  except ValueError:failed.append(index)
 need(len(failed)==1 and len(good)==4,'epoch-header-fallback-requires-exact-four-facts');_header_order([good[i]for i in sorted(good)]);missing=failed[0]
 return {'kind':'finite-single-header-query-locator-plan-v1','image':p['image'],'cells':[{'key':'header-range-locator','box':want['box'],'queries':{'header'+str(missing):HEADER[missing]}}],'failed_index':missing,'cached_facts':[good.get(i)for i in range(5)],'first_pass_is_locator_only':True}
def header_fallback_ROI(p,first,locator):
 lp=header_fallback_plan(p,first);missing=lp['failed_index'];label=HEADER[missing];field='header'+str(missing);good=lp['cached_facts'];_header_method(locator);need(len(locator.get('cells',[]))==1,'epoch-header-locator-cell-count');cell=locator['cells'][0];need(set(cell)=={'key','box','observations','ranges'}and cell['key']==lp['cells'][0]['key']and cell['box']==lp['cells'][0]['box'],'epoch-header-locator-cell-binding');w,h=p['image']['width'],p['image']['height'];candidates=[]
 for index,r in enumerate(cell['ranges']):
  need(set(r)=={'field','text','box','confidence'}and r['field']==field and r['text']==label and type(r['confidence'])in(int,float)and math.isfinite(r['confidence'])and 0<=r['confidence']<=1,'epoch-header-query-literal');_header_bounds(r['box'],w,h,1);ordered=[r if i==missing else good[i]for i in range(5)]
  try:_header_order(ordered);candidates.append((index,r))
  except ValueError:pass
 need(len(candidates)==1,'epoch-header-range-not-unique');index,hint=candidates[0];b=hint['box'];owners=[]
 for i,r in enumerate(cell['observations']):
  if type(r.get('text'))is not str or r['text'].count(label)!=1:continue
  _header_bounds(r['box'],w,h,1);a=r['box']
  if a[0]-1/w<=b[0] and b[0]+b[2]<=a[0]+a[2]+1/w and a[1]-1/h<=b[1] and b[1]+b[3]<=a[1]+a[3]+1/h:owners.append((i,r))
 need(len(owners)==1,'epoch-header-range-owner-not-unique');box=[max(0,math.floor(b[0]*w)-2),max(0,math.floor((1-b[1]-b[3])*h)-2),min(w,math.ceil((b[0]+b[2])*w)+2),min(h,math.ceil((1-b[1])*h)+2)];need(0<=box[0]<box[2]<=w and 0<=box[1]<box[3]<=h,'epoch-header-ROI-bounds')
 return {'kind':'finite-single-header-range-ROI-v1','image':p['image'],'cells':[{'key':field,'box':box,'expected':label}],'range_index':index,'range':hint,'owner_index':owners[0][0],'owner':owners[0][1],'padding_pixels':2,'estimated_box_overshoot_limit_pixels':1,'first_pass_is_locator_only':True,'DOM_per_selector_geometry_claimed':False}
def epoch_header_checks(p,first,fallback=None):
 try:checks=fragment_evaluate(p,first)
 except ValueError:checks=None
 if checks is not None:need(fallback is None,'epoch-header-unnecessary-fallback');return checks
 need(isinstance(fallback,dict)and set(fallback)=={'locator_runtime','locator_plan','locator','locator_stderr','second_plan','second','second_stderr','ROI_pixels','locator_returncode','second_returncode'},'epoch-header-fallback-receipt');need(fallback['locator_runtime']==locator_runtime() and fallback['locator_returncode']==fallback['second_returncode']==0,'epoch-header-fallback-runtime-or-exit')
 lp=header_fallback_plan(p,first);need(document(fallback['locator_plan'])==lp,'epoch-header-locator-plan-changed');roi=header_fallback_ROI(p,first,document(fallback['locator']));need(document(fallback['second_plan'])==roi and fallback['ROI_pixels']==pixel_refs(roi),'epoch-header-ROI-changed');second=document(fallback['second']);_header_method(second);need(len(second.get('cells',[]))==1,'epoch-header-second-cell-count');box=roi['cells'][0]['box'];rw,rh=box[2]-box[0],box[3]-box[1]
 for r in second['cells'][0]['observations']:_header_bounds(r['box'],rw,rh)
 literal=evaluate(roi,second)[0]['observed_text'];rows=second['cells'][0]['observations'];w,h=p['image']['width'],p['image']['height'];left=min(r['box'][0]for r in rows);bottom=min(r['box'][1]for r in rows);right=max(r['box'][0]+r['box'][2]for r in rows);top=max(r['box'][1]+r['box'][3]for r in rows);globalbox=[(box[0]+left*rw)/w,(h-box[3]+bottom*rh)/h,(right-left)*rw/w,(top-bottom)*rh/h];_header_bounds(globalbox,w,h);good=lp['cached_facts'];missing=lp['failed_index'];allrows=[{'text':literal,'confidence':min(r['confidence']for r in rows),'box':globalbox}if i==missing else good[i]for i in range(5)];_header_order(allrows)
 for name in ('locator_plan','locator','locator_stderr','second_plan','second','second_stderr'):data(fallback[name])
 return {'header_checks':[{'header':label,'observed_text':r['text'],'confidence':r['confidence'],'whole_region_normalized_box':r['box'],'evidence':'independent-range-ROI-second'if i==missing else 'first-strict-header-fact'}for i,(label,r)in enumerate(zip(HEADER,allrows))],'unverified_other_OCR_observations':copy.deepcopy(first['cells'][0]['observations']),'full_date_visible':False,'full_date_certified':False,'per_selector_OCR_geometry_claimed':False,'fallback_single_header':missing,'history_resolved':False,'row_fields_certified':False}
def cached_header_evidence(release_ref,preview_ref,source,p):
 release=document(release_ref);need(release.get('kind')=='supervisor-reviewed-source-release-v1' and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director','epoch-header-cache-reviewed-release');targets=release['targets'];need(len({t['target']for t in targets})==len(targets),'epoch-header-cache-duplicate-target');code=code_refs()[0];hits=[t for t in targets if t['target']==code['path']];need(len(hits)==1 and hits[0]['after']['sha256']==code['sha256'],'epoch-header-cache-current-Q-pin');authority=release['anchor_pixel_quality_cached_evaluation'];need(set(authority)=={'kind','preview','source','evaluation_result','evaluation_freeze','evaluation_script'}and authority['kind']=='root-pinned-anchor-header-fallback-evidence-v1' and authority['preview']==preview_ref and authority['source']==source,'epoch-header-cache-exact-authority');freeze=document(authority['evaluation_freeze']);need(freeze.get('kind')=='one-shot-query-range-then-independent-ROI-evaluation-freeze-v1' and freeze.get('status')=='pixel-pass-not-business-approved' and freeze.get('no_attestation')is True and freeze.get('no_source_changes')is True,'epoch-header-cache-freeze');need(authority['evaluation_result']in freeze['files'] and authority['evaluation_script']in freeze['files'],'epoch-header-cache-result-script-closure')
 for r in freeze['files']:data(r)
 v=document(authority['evaluation_result']);need(v.get('kind')=='fixed-query-range-then-independent-literal-ROI-OCR-evaluation-v1' and v.get('status')=='pixel-evaluation-pass-not-business-approved' and v['preview']==preview_ref and v['locator_invocations']==v['second_invocations']==1 and v['original_refs_unchanged']is True and all(v.get(k)is False for k in ('attestation_generated','approved','accepted','history_resolved','row_fields_certified')),'epoch-header-cache-evaluation');first=document(v['first']);lp=header_fallback_plan(p,first);locator=document(v['locator']['stdout']);roi=header_fallback_ROI(p,first,locator)
 # Experiment plan labels differ; facts/cells/queries are recomputed, not trusted.
 cachedlp=document(v['locator']['plan']);need(cachedlp['image']==lp['image'] and cachedlp['cells']==lp['cells'],'epoch-header-cache-locator-input');cachedroi=document(v['ROI']);need(cachedroi['image']==roi['image'] and cachedroi['cells']==roi['cells'] and all(cachedroi[k]==roi[k]for k in ('range_index','range','owner_index','owner')) and v['ROI_pixels']==pixel_refs(roi) and document(v['second']['plan'])==cachedroi,'epoch-header-cache-ROI-input');need(v['locator_runtime']==locator_runtime() and v['second']['binary']==runtime(),'epoch-header-cache-binary');need(v['locator']['returncode']==v['second']['returncode']==0,'epoch-header-cache-exit')
 # Return only checked evidence; producer publishes canonical recomputed plans.
 return {'first':v['first'],'locator':v['locator']['stdout'],'locator_stderr':v['locator']['stderr'],'second':v['second']['stdout'],'second_stderr':v['second']['stderr'],'locator_plan_value':lp,'ROI_value':roi,'locator_runtime':v['locator_runtime'],'cached_release':release_ref}


def verify_epoch_stage_exit(exitref,binary,stdout):
 value=document(exitref);dispatch=document(value['dispatch']);plan=document(value['plan']);argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',binary['path'],plan['image']['path'],value['plan']['path']]
 need(value.get('kind')=='epoch-header-OCR-natural-exit-v1' and type(value.get('returncode'))is int and value['returncode']==0 and value['stdout']==stdout and value['binary']==binary and value['argv']==argv and value['PID_available']is False,'epoch-header-natural-exit-binding')
 need(dispatch=={'kind':'epoch-header-OCR-dispatch-intent-v1','stage':value['stage'],'argv':argv,'binary':binary,'plan':value['plan'],'started_at':value['started_at'],'started_monotonic':value['started_monotonic'],'PID_available':False},'epoch-header-dispatch-binding')
 need(all(type(value[k])in(int,float)and math.isfinite(value[k])for k in ('started_monotonic','exited_monotonic','elapsed_seconds'))and value['exited_monotonic']>=value['started_monotonic'] and value['elapsed_seconds']==value['exited_monotonic']-value['started_monotonic'] and datetime.datetime.fromisoformat(value['started_at'])<=datetime.datetime.fromisoformat(value['exited_at']),'epoch-header-stage-time')
 for r in (value['dispatch'],value['plan'],value['stdout'],value['stderr'],binary):data(r)
 return value
