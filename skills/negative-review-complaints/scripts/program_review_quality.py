"""Finite original single-card OCR quality. No business action or capture."""
import copy,hashlib,json,math,subprocess,time,os,sys,re
from pathlib import Path
import review_capture as rc
KIND='complaint-region-program-quality-v1'
METHOD='ScreenCaptureKit/SCScreenshotManager/desktopIndependentWindow'
RUNTIME_PIN={'kind': 'local-review-quality-runtime-v1', 'swift_sha256': '9ab7203779cb871e83453987d93a1811bc59ae80dda417655c53b9bc4858faa8', 'binary_sha256': 'ca497b0f4e5e4b90d08db990e0af96a736049369175cd6fbeacf24fa35df800d'}
SCORES={1:'非常差',2:'较差',3:'一般'}
need=rc.require
ROOT=Path(rc.__file__).resolve().parents[3]
def ref(path):return rc.ref(path)
def raw(r):
 p=Path(r['path']);need(p.is_absolute()and p.resolve()==p and not any(x.is_symlink()for x in(p,*p.parents)),'review-quality-canonical-ref');b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==r['sha256'],'review-quality-reference-changed');return b
def doc(r):return json.loads(raw(r))
def runtime():
 folder=Path(__file__).resolve().parent;manifest=folder/'review-quality-runtime.json';need(doc(ref(manifest))==RUNTIME_PIN,'review-quality-runtime-manifest')
 need(rc.sha(folder/'review-quality-ocr.swift')==RUNTIME_PIN['swift_sha256']and rc.sha(folder/'review-quality-ocr')==RUNTIME_PIN['binary_sha256'],'review-quality-runtime-changed');return ref(folder/'review-quality-ocr')
def code():return [ref(Path(__file__)),ref(Path(rc.__file__)),ref(Path(__file__).with_name('review-quality-ocr.swift')),ref(Path(__file__).with_name('review-quality-runtime.json'))]
LEGACY_Q_SHA='5f85ffec757e8fb051cda229282b99c7cc5b37b7a2b341d7f1487dd33b99eb86'
def legacy_quality_code():return {'path':str(ROOT/'skills/negative-review-complaints/scripts/program_review_quality.py'),'sha256':LEGACY_Q_SHA}
def quality_code_bytes(reference):
 # Only the completed first card's exact Q version is archival CODE data.
 # No archived Python is imported or executed; all other refs stay strict raw.
 if reference==legacy_quality_code():return raw({'path':str(ROOT/'work/performance-audit/complaint-quality-score-range-candidate/program_review_quality.py.before'),'sha256':LEGACY_Q_SHA})
 if reference['path']==str(ROOT/'skills/negative-review-complaints/scripts/program_review_quality.py'):
  import execution_timing as timing
  material=timing.configuration_source_material(reference);return raw(material['material'])
 return raw(reference)
def quality_codes(references):
 current=code();need(references==current or (len(references)==len(current)==4 and references[0]['path']==str(ROOT/'skills/negative-review-complaints/scripts/program_review_quality.py') and references[1:]==current[1:]),'review-quality-exact-current-or-prior-code')
 for r in references:quality_code_bytes(r)
 return True
def compact(s):return ''.join(s.split())
def body_text(s):
 # Typography only: ordinary one/two ASCII periods remain punctuation.
 return re.sub(r'[.\u2026\u22ef]+',lambda m:'…' if any(c in m.group()for c in '…⋯')or len(m.group())>=3 else m.group(),compact(s))
def body_runs(value,pool,width,height):
 # Keep the original raw-exact result (and old attestations) unchanged.
 try:return runs(value,pool,width,height)
 except ValueError as error:
  if str(error)!='review-quality-visible-text-ambiguous-or-missing:'+value:raise
 return runs(value,pool,width,height,body_text,joined=True)
def walk(n):
 yield n
 for c in n.get('children',[]):yield from walk(c)
def one(xs,reason):need(len(xs)==1,reason);return xs[0]
def klass(n):return n.get('attributes',{}).get('class','')
def plan(m):
 need(m['kind']=='normal-review-region-registration-v1'and m['image_scope']=='derived-dom-review-region'and m['whole_window']is False,'review-quality-region-only')
 p=m['proof_before'];need(p==m['proof_after']and m['geometry_before']==m['geometry_after'],'review-quality-proof-race');need(len(p['base_proof']['reviews'])==len(m['review_keys'])==1,'review-quality-exact-one-card')
 capture=doc(m['capture_metadata']);need(capture['capture_method']==METHOD and capture['state']=='complete'and capture['png']==m['derivation']['source'],'review-quality-single-window')
 need(capture['before']['window']==capture['after']['window']and capture['before']['scope']==capture['after']['scope'],'review-quality-native-race')
 review=p['base_proof']['reviews'][0];need(review['review_key']==m['review_keys'][0]and p['selectors']==[review['card']]and review['card_visible']is True,'review-quality-card-binding')
 g=review['geometry'];need(all(g[k]['fully_visible']is True for k in('store','customer','heart'))and all(g['body'][k]is True for k in('rendered','visible_region','unsupported_css_absent')),'review-quality-fields-not-rendered')
 source=doc(m['source']);key=m['review_keys'][0];row=one([r for r in source['rows']if source['groupid']+':'+r['review_id']==key],'review-quality-source-key')
 need(all(review[k]==row[{'body':'text'}.get(k,k)]for k in('store','customer','body'))and p['review_action']==row['action'],'review-quality-source-fields')
 page=doc(m['page']);card=one([n for n in walk(page['tree']['root'])if n.get('selector')==review['card']],'review-quality-original-card');children=card.get('children',[])
 need(len(children)in(1,2)and klass(children[0])=='main-OjCeVu'and (len(children)==1 or klass(children[1])=='reply-BbhyhW'),'review-quality-known-card-layout')
 cols=children[0]['children'];need([klass(n)for n in cols]==['firstColumn-aItX1o','secondColumn-NC8I04','poiColumn-dQUMXM','customAndButtonColumn-GlYUOL'],'review-quality-four-column-layout')
 caption=one([n for n in walk(cols[0])if klass(n)=='text-J4lpcH'],'review-quality-score-caption');stars=row['stars'];need(type(stars)is int and stars in SCORES and caption.get('name')==SCORES[stars],'review-quality-known-score-label')
 need(type(review['body'])is str and bool(review['body'].strip()),'review-quality-image-only-body-unsupported')
 return {'kind':'program-review-card-plan-v1','image':m['image'],'review_key':key,'source':m['source'],'fields':{'score':SCORES[stars],'store':row['store'],'customer':row['customer'],'body_visible_fragment':row['text'],'action':row['action']},'source_score':stars,'original_body_complete_flag':review['text_complete_in_image'],'has_merchant_reply':len(children)==2,'source_has_customer_badge':any(klass(n)=='userTagImage-gsqjn0' for n in walk(cols[3])),'cells':[{'key':'single-original-card','box':[0,0,m['image']['width'],m['image']['height']],'queries':{'customer':row['customer'],'score':SCORES[stars],'action':row['action']}}]}

def store_text(s):return compact(s).replace('（','(').replace('）',')')
def score_text(s):
 # Observed score caption decoration only; never fuzzy-match or fill letters.
 value=compact(s);return value[1:] if value.startswith('•') else value
def observations(cell,width,height,minconf=0):
 rows=[]
 for i,r in enumerate(cell['observations']):
  b=r['box']
  if cell.get('coordinate_system')=='top-left-pixel-quadrilateral':
   need(len(b)==4 and all(type(point)is list and len(point)==2 and all(type(v)in(int,float)and math.isfinite(v)for v in point)for point in b),'review-quality-Rapid-polygon')
   left,right=min(point[0]for point in b),max(point[0]for point in b);top,bottom=min(point[1]for point in b),max(point[1]for point in b);b=[left/width,1-bottom/height,(right-left)/width,(bottom-top)/height]
  need(type(r['text'])is str and r['text']and type(r['confidence'])in(int,float)and math.isfinite(r['confidence'])and 0<=r['confidence']<=1 and len(b)==4 and all(type(v)in(int,float)and math.isfinite(v)for v in b),'review-quality-OCR-value')
  need(b[2]>0 and b[3]>0 and b[0]>=-1/width and b[1]>=-1/height and b[0]+b[2]<=1+1/width and b[1]+b[3]<=1+1/height,'review-quality-OCR-outside-region')
  if r['confidence']>=minconf:rows.append({'index':i,'text':r['text'],'left':b[0],'top':1-b[1]-b[3],'right':b[0]+b[2],'bottom':1-b[1],'height':b[3]})
 return rows

def runs(value,pool,width,height,norm=compact,joined=False):
 target=norm(value);found=[]
 def prefix(text):return target.startswith(text)or(joined and text.endswith('.')and target.startswith(text.rstrip('.')+'…'))
 def extend(chain,text):
  if text==target:found.append(chain);return
  if not prefix(text)or len(chain)>=24:return
  last=chain[-1]
  for r in pool:
   if r['index']in [x['index']for x in chain]:continue
   # Vision may split one rendered line into adjacent observations. Exact
   # string concatenation is required; overlap permits only subpixel rounding.
   lineheight=max(last['height'],r['height']);overlap=min(last['bottom'],r['bottom'])-max(last['top'],r['top'])
   inline=(r['left']>last['left']and r['right']>last['right']and -1/width<=r['left']-last['right']<=max(2/width,.5*lineheight*height/width)and overlap>=.5*min(last['height'],r['height'])and abs(r['top']-last['top'])<=.5*lineheight)
   newline=(r['top']>=last['bottom']-.2*last['height']and r['top']-last['bottom']<=2*lineheight and abs(r['left']-chain[0]['left'])<=2*max(r['height']*height/width,chain[0]['height']*height/width))
   if not(inline or newline):continue
   extend(chain+[r],norm(''.join(x['text']for x in chain+[r]))if joined else text+norm(r['text']))
 for r in pool:
  text=norm(r['text'])
  if prefix(text):extend([r],text)
 return one(found,'review-quality-visible-text-ambiguous-or-missing:'+value)

def method(ocr):
 if ocr.get('kind')==RAPID_KIND:
  need(ocr.get('engine')==RAPID_ENGINE and all(c.get('coordinate_system')=='top-left-pixel-quadrilateral'for c in ocr['cells']),'review-quality-Rapid-method');provenance=ocr['provenance'];runtime=rapid_runtime();need(provenance['runtime']==runtime['manifest'] and provenance['runner']==runtime['runner'] and all(v==['CPUExecutionProvider']for v in provenance['providers'].values()) and set(provenance['providers'])=={'text_det','text_cls','text_rec'} and provenance['post_import_network_attempts']==[] and provenance['expected_text_supplied']is False,'review-quality-Rapid-provenance')
  need(type(ocr.get('elapsed_seconds'))in(int,float)and math.isfinite(ocr['elapsed_seconds'])and ocr['elapsed_seconds']>=0,'review-quality-Rapid-time');return
 need(ocr.get('kind')=='local-vision-cell-ocr-v1'and ocr.get('recognition_level')=='accurate'and ocr.get('recognition_languages')==['zh-Hans','en-US']and ocr.get('language_correction')is False and ocr.get('CPU_only')is True,'review-quality-OCR-method')
 need(type(ocr.get('elapsed_seconds'))in(int,float)and math.isfinite(ocr['elapsed_seconds'])and ocr['elapsed_seconds']>=0,'review-quality-OCR-time')

def localize(p,first):
 method(first);need(len(first['cells'])==1 and first['cells'][0]['key']=='single-original-card'and first['cells'][0]['box']==p['cells'][0]['box'],'review-quality-OCR-card-binding')
 w,h=p['image']['width'],p['image']['height'];cell=first['cells'][0];rows=observations(cell,w,h)
 exact=lambda value:one([r for r in rows if compact(r['text'])==compact(value)],'review-quality-locator:'+value)
 score_hits=[r for r in rows if score_text(r['text'])==compact(p['fields']['score'])];action=exact(p['fields']['action']);store=runs(p['fields']['store'],rows,w,h,store_text);storeleft=min(r['left']for r in store);score_locator=None
 if score_hits:score=one(score_hits,'review-quality-locator:'+p['fields']['score'])
 else:
  # Fixed source query range is a first-pass ROI hint, not recognition proof.
  # Adjacent heart/avatar OCR glyphs are not added to the source score text.
  candidates=[(i,r)for i,r in enumerate(cell['ranges'])if r.get('field')=='score'];index,hint=one(candidates,'review-quality-score-range-not-unique')
  need(set(hint)=={'field','text','box','confidence'} and hint['text']==p['fields']['score'] and p['fields']['score']==SCORES[p['source_score']],'review-quality-score-range-source')
  score=one(observations({'observations':[{'text':hint['text'],'box':hint['box'],'confidence':hint['confidence']}]},w,h),'review-quality-score-range-invalid')
  owners=[r for r in rows if compact(r['text']).count(compact(hint['text']))==1 and r['left']-1/w<=score['left'] and score['right']<=r['right']+1/w and r['top']-1/h<=score['top'] and score['bottom']<=r['bottom']+1/h];owner=one(owners,'review-quality-score-range-observation-not-unique')
  need(score['right']<storeleft and abs(score['top']-store[0]['top'])<=.75*max(score['height'],store[0]['height']),'review-quality-score-range-header-column')
  score_locator={'method':'fixed-source-query-range-locator-only-v1','range_index':index,'observation_index':owner['index'],'surrounding_OCR_glyphs_certified':False}
 # Native Vision range boxes are approximate WORD-level hints, not proof. Keep
 # padding and require independent >=0.5 recognition of exact source text below.
 header_top=min(score['top'],store[0]['top']);header_height=max(score['height'],store[0]['height'])
 ranges=[r for r in cell['ranges']if r['field']=='customer'and r['text']==p['fields']['customer']and len(r['box'])==4 and max(x['right']for x in store)<r['box'][0]and r['box'][0]+r['box'][2]<action['left']and abs(1-r['box'][1]-r['box'][3]-header_top)<=.75*max(header_height,r['box'][3])];locator=None
 if first.get('kind')==RAPID_KIND and not ranges:
  native=one([r for r in rows if compact(r['text'])==compact(p['fields']['customer']) and max(x['right']for x in store)<r['left'] and r['right']<action['left'] and abs(r['top']-header_top)<=.75*max(header_height,r['height'])],'review-quality-Rapid-exact-customer-locator');ranges=[{'field':'customer','text':native['text'],'box':[native['left'],1-native['bottom'],native['right']-native['left'],native['height']],'confidence':cell['observations'][native['index']]['confidence']}];locator={'method':'exact-native-Rapid-observation-locator-only-v1','observation_index':native['index']}
 if ranges:customer_range=one(ranges,'review-quality-nickname-range-unavailable');b=customer_range['box']
 else:
  # A first-pass hint is never nickname proof. Only locate the unique header
  # word between the independently recognized store and action columns. The
  # second OCR must still recognize the literal source name with >=0.5.
  import re
  header=[r for r in rows if max(x['right']for x in store)<r['left']and r['right']<action['left']and abs(r['top']-header_top)<=.75*max(header_height,r['height'])]
  badge=[r for r in header if p['source_has_customer_badge']and re.fullmatch(r'[\[［({IlL|]*[lL][vV][.·,]?[0-9]{1,2}[\]］)}]*',compact(r['text']))]
  need(len(badge)<=1,'review-quality-header-badge-not-unique');candidate=one([r for r in header if r not in badge],'review-quality-nickname-range-unavailable')
  need(not badge or candidate['right']<badge[0]['left'],'review-quality-header-badge-order-invalid');b=[candidate['left'],1-candidate['bottom'],candidate['right']-candidate['left'],candidate['height']];locator={'method':'unique-header-observation-locator-only-v1','observation_index':candidate['index'],'excluded_badge_indices':[r['index']for r in badge]}
 need(len(b)==4 and all(type(v)in(int,float)and math.isfinite(v)for v in b),'review-quality-range-box')
 customer={'left':b[0],'top':1-b[1]-b[3],'right':b[0]+b[2],'bottom':1-b[1],'height':b[3]}
 need(score['right']<storeleft and max(r['right']for r in store)<customer['left']and customer['right']<action['left'],'review-quality-column-order')
 top=min(score['top'],customer['top'],store[0]['top']);lineheight=max(score['height'],customer['height'],store[0]['height']);need(abs(customer['top']-top)<=.75*lineheight,'review-quality-customer-top-row')
 replytop=1.0
 if p['has_merchant_reply']:replytop=one([r for r in rows if compact(r['text']).startswith('商家回复')],'review-quality-reply-boundary-missing')['top']
 body=body_runs(p['fields']['body_visible_fragment'],[r for r in rows if r['left']>score['right']and r['right']<storeleft and r['bottom']<=replytop],w,h)
 need(abs(body[0]['top']-top)<=.75*lineheight and all(r['bottom']<=replytop for r in [score,customer,action,*store]),'review-quality-main-card-fields')
 groups={'score':[score],'body_visible_fragment':body,'store':store,'customer':[customer],'action':[action]};cells=[]
 for key,items in groups.items():
  pad=max(2,math.ceil(max(r['height']for r in items)*h*.15));box=[max(0,math.floor(min(r['left']for r in items)*w)-pad),max(0,math.floor(min(r['top']for r in items)*h)-pad),min(w,math.ceil(max(r['right']for r in items)*w)+pad),min(h,math.ceil(max(r['bottom']for r in items)*h)+pad)]
  cells.append({'key':key,'box':box})
 result={'kind':'program-review-derived-ROI-v1','image':p['image'],'cells':cells,'derivation':'original-card-OCR-boxes-and-verified-column-semantics','first_pass_is_locator_only':True}
 if locator is not None:result['nickname_locator']=locator
 if score_locator is not None:result['score_locator']=score_locator
 return result

CONTEXT_ROI_METHOD='fixed-half-cell-context-original-pixel-fields-v1'
def context_roi(p,first):
 # One fixed, query-free context expansion; no recognition-result parameter.
 base=localize(p,first);result=copy.deepcopy(base);w,h=p['image']['width'],p['image']['height']
 for cell in result['cells']:
  left,top,right,bottom=cell['box'];pad=max(8,math.ceil((bottom-top)/2))
  cell['box']=[max(0,left-pad),max(0,top-pad),min(w,right+pad),min(h,bottom+pad)]
 result['context_expansion']={'method':CONTEXT_ROI_METHOD,'base_ROI':base,'padding':'max(8,ceil(original_cell_height/2)) original pixels on each side; image bounds clipped','expected_text_supplied_to_engine':False}
 return result

def evaluate(p,ocr,roi):
 method(ocr);need(len(ocr['cells'])==len(roi['cells'])==5,'review-quality-five-fields-required');checks={}
 for want,cell in zip(roi['cells'],ocr['cells']):
  need(cell['key']==want['key']and cell['box']==want['box'],'review-quality-field-ROI-binding');key=want['key'];w,h=want['box'][2]-want['box'][0],want['box'][3]-want['box'][1];rows=observations(cell,w,h,.5);expected=p['fields'][key]
  if key=='customer':
   candidates=[]
   for r in rows:
    text=compact(r['text']);target=compact(expected)
    if target not in text:continue
    prefix,suffix=text.split(target,1)
    # Only existing avatar/level-image adornment; no nickname from reply text.
    import re
    if prefix not in ('','•','·','●','○'):continue
    if suffix and not(p['source_has_customer_badge']and re.fullmatch(r'[IlL|]*[lL][vV][.·,]?[0-9]{1,2}',suffix)):continue
    candidates.append(r)
   chosen=[one(candidates,'review-quality-literal-nickname-missing')]
  else:chosen=body_runs(expected,rows,w,h)if key=='body_visible_fragment'else runs(expected,rows,w,h,store_text if key=='store'else score_text if key=='score'else compact)
  checks[key]={'expected':expected,'observed_text':' '.join(r['text']for r in chosen),'observation_indices':[r['index']for r in chosen],'box':want['box']}
 checks['body_visible_fragment'].update(full_source_text_observed=True,original_text_complete_flag_retained=p['original_body_complete_flag'])
 body=checks['body_visible_fragment']
 # Raw OCR remains in the native output; this is explicitly not raw equality.
 if compact(body['expected'])!=compact(body['observed_text']):
  need(body_text(body['expected'])==body_text(body['observed_text']),'review-quality-body-typography')
  body['comparison']={'kind':'body-ellipsis-typographic-equivalence-v1','raw_expected':body['expected'],'raw_observed':body['observed_text'],'normalized_expected':body_text(body['expected']),'normalized_observed':body_text(body['observed_text']),'raw_text_equal':False,'scope':'body-visible-fragment-only','run_characters':['U+2026','U+22EF','U+002E'],'ordinary_one_or_two_ASCII_periods_preserved':True}
 checks['score']['source_value']=p['source_score'];return checks

def verify(a_ref,m):
 import review_region_capture as region
 a=doc(a_ref)
 if a.get('producer_method')==RAPID_METHOD:return verify_rapid(a_ref,m)
 need(a.get('kind')==KIND and a.get('decision')=='finite-card-fields-verified'and a.get('producer_method')=='local-Vision-original-single-card-v1'and 'reviewer_role'not in a,'review-quality-program-kind')
 preview=doc(a['registration_preview']);expected=copy.deepcopy(m)
 for k in('quality_attestation','quality_approved_at'):expected.pop(k,None)
 expected['state']='awaiting-visual-review';need(preview==expected,'review-quality-original-preview')
 region.verify(a['registration_preview']['path'],allow_preview=True)
 p=plan(preview);receipt=doc(a['receipt']);need(receipt.get('kind')=='program-review-quality-receipt-v1'and quality_codes(a['code'])and a['binary']==runtime()and receipt['plan']==p and receipt['preview']==a['registration_preview']and receipt['binary']==a['binary']and receipt['code']==a['code'],'review-quality-receipt-binding')
 need(receipt['image']==preview['image']and receipt['image_sha256']==hashlib.sha256(raw(preview['image'])).hexdigest(),'review-quality-receipt-pixels');first=doc(receipt['first_ocr']);roi=localize(p,first);need(receipt['roi']==roi,'review-quality-ROI-changed');checks=evaluate(p,doc(receipt['ocr']),roi);need(a['checks']==checks,'review-quality-checks-changed')
 need(rc.authority.stamp(preview['recorded_at'])<=rc.authority.stamp(a['checked_at'])<=rc.authority.stamp(m['quality_approved_at']),'review-quality-time')
 for r in(a['registration_preview'],a['receipt'],receipt['first_ocr'],receipt['ocr'],a['binary'],*a['code']):quality_code_bytes(r)
 return a

def create(preview_ref,outdir):
 import review_region_capture as region
 m=doc(preview_ref);need(m['state']=='awaiting-visual-review','review-quality-awaiting-original');region.verify(preview_ref['path'],allow_preview=True)
 out=Path(outdir).resolve();final=out/'quality.json'
 if out.exists():
  if not final.exists():return refine_saved(preview_ref,out)
  verify(ref(final),{**m,'state':'complete','quality_approved_at':rc.stamp()});return ref(final)
 out.mkdir(parents=True);(out/'intent.json').write_text(json.dumps({'kind':'program-review-quality-intent-v1','preview':preview_ref,'code':code(),'created_at':rc.stamp()}));start=time.monotonic()
 try:
  p=plan(m);(out/'plan.json').write_text(json.dumps(p,ensure_ascii=False));binary=runtime();run=subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',binary['path'],p['image']['path'],str(out/'plan.json')],capture_output=True,timeout=60)
  (out/'first-ocr.json').write_bytes(run.stdout);(out/'first-ocr.stderr').write_bytes(run.stderr);need(run.returncode==0,'review-quality-OCR-process-failed');roi=localize(p,doc(ref(out/'first-ocr.json')));(out/'roi.json').write_text(json.dumps(roi,ensure_ascii=False));run=subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',binary['path'],p['image']['path'],str(out/'roi.json')],capture_output=True,timeout=60);(out/'ocr.json').write_bytes(run.stdout);(out/'ocr.stderr').write_bytes(run.stderr);need(run.returncode==0,'review-quality-local-OCR-process-failed');checks=evaluate(p,doc(ref(out/'ocr.json')),roi)
  receipt={'kind':'program-review-quality-receipt-v1','preview':preview_ref,'image':p['image'],'image_sha256':hashlib.sha256(raw(p['image'])).hexdigest(),'plan':p,'binary':binary,'code':code(),'first_ocr':ref(out/'first-ocr.json'),'roi':roi,'ocr':ref(out/'ocr.json'),'pipeline_elapsed_seconds':time.monotonic()-start};(out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False))
  region.verify(preview_ref['path'],allow_preview=True);raw(preview_ref);raw(p['image']);raw(m['derivation']['source']);raw(binary)
  a={'kind':KIND,'decision':'finite-card-fields-verified','producer_method':'local-Vision-original-single-card-v1','registration_preview':preview_ref,'code':code(),'binary':binary,'receipt':ref(out/'receipt.json'),'checks':checks,'checked_at':rc.stamp()};final.write_text(json.dumps(a,ensure_ascii=False));return ref(final)
 except Exception as e:
  (out/'exception.json').write_text(json.dumps({'kind':'program-review-quality-exception-v1','preview':preview_ref,'reason':str(e),'elapsed_seconds':time.monotonic()-start}))
  if 'p'in locals()and recognition_failure(str(e),p):return refine_saved(preview_ref,out)
  raise

# Independent typed local engine. Legacy Vision schemas/method are unchanged.
RAPID_KIND='local-rapidocr-native-cell-observations-v1'
RAPID_METHOD='local-RapidOCR-original-single-card-v1'
RAPID_ENGINE={'rapidocr':'3.10.0','onnxruntime':'1.19.2','provider':'CPUExecutionProvider','text_score':.5}
RAPID_MANIFEST_SHA='8d07ee49d8e9a99b6a26c6e576e41977f3e5f7f854e1ea14bfe7037e3cdf1812'
RAPID_RUNNER_SHA='92e4e8678326a90f2695c750f98d51ba72c615502c7d559863c83bb012c88a91'
def rapid_runtime():
 manifest={'path':str(ROOT/'skills/negative-review-complaints/runtime/rapidocr-cpu-v1/manifest.json'),'sha256':RAPID_MANIFEST_SHA};runner={'path':str(ROOT/'skills/negative-review-complaints/scripts/local_rapid_quality.py'),'sha256':RAPID_RUNNER_SHA};m=doc(manifest);raw(runner);need(m['kind']=='offline-RapidOCR-CPU-wheelhouse-v1'and m['engine']==RAPID_ENGINE and m['runner_sha256']==runner['sha256'],'review-quality-Rapid-runtime');return {'manifest':manifest,'runner':runner,'python':str(Path(manifest['path']).parent/'.venv/bin/python')}
def recognition_failure(error,p):
 return error in {'review-quality-visible-text-ambiguous-or-missing:'+v for v in p['fields'].values()}|{'review-quality-locator:'+v for v in p['fields'].values()}|{'review-quality-nickname-range-unavailable','review-quality-literal-nickname-missing','review-quality-score-range-not-unique'}
def _quality_immutable(path,value):
 path=Path(path);data=json.dumps(value,ensure_ascii=False,sort_keys=True).encode()
 if path.exists():need(path.read_bytes()==data,'review-quality-immutable-conflict');return ref(path)
 path.parent.mkdir(parents=True,exist_ok=True);fd=os.open(str(path),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
 with os.fdopen(fd,'wb')as handle:handle.write(data);handle.flush();os.fsync(handle.fileno())
 return ref(path)
def failed_quality_prefix(preview_ref,out,p):
 out=Path(out);need(out==Path(preview_ref['path']).parent/'program-quality'and not (out/'quality.json').exists(),'review-quality-exact-failed-output');names=['intent.json','plan.json','first-ocr.json','first-ocr.stderr','exception.json'];names.extend(n for n in ('roi.json','ocr.json','ocr.stderr')if(out/n).exists());references=[ref(out/n)for n in names];documents={Path(r['path']).name:doc(r)for r in references if r['path'].endswith('.json')};intent=documents['intent.json'];exception=documents['exception.json'];need(intent['kind']=='program-review-quality-intent-v1'and intent['preview']==exception['preview']==preview_ref and documents['plan.json']==p and recognition_failure(exception['reason'],p),'review-quality-known-recognition-failure');quality_codes(intent['code']);method(documents['first-ocr.json']);return references

def rapid_call(runtime,image,plan,path):
 path=Path(path);receipt_path=path/'exit.json';plan_ref=_quality_immutable(path/'plan.json',plan);argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',runtime['python'],'-I','-B',runtime['runner']['path'],'ocr','--manifest',runtime['manifest']['path'],'--manifest-sha',runtime['manifest']['sha256'],'--image',image['path'],'--image-sha',image['sha256'],'--plan',plan_ref['path'],'--plan-sha',plan_ref['sha256']]
 if receipt_path.exists():verify_rapid_call(ref(receipt_path),runtime,image,plan_ref);return doc(ref(receipt_path))['stdout'],ref(receipt_path)
 need(not(path/'launch.json').exists(),'review-quality-local-OCR-unresolved-readonly');_quality_immutable(path/'launch.json',{'kind':'local-RapidOCR-launch-v1','argv':argv,'image':image,'plan':plan_ref,'runtime':runtime,'at':rc.stamp()});started=time.monotonic();run=subprocess.run(argv,capture_output=True,timeout=125)
 # Each result is immutable; no existing failed/unknown invocation is replayed.
 for name,data in [('stdout.json',run.stdout),('stderr.txt',run.stderr)]:
  destination=path/name;need(not destination.exists(),'review-quality-local-output-conflict');destination.write_bytes(data)
 receipt={'kind':'local-RapidOCR-natural-exit-v1','argv':argv,'launch':ref(path/'launch.json'),'image':image,'plan':plan_ref,'runtime':runtime,'returncode':run.returncode,'stdout':ref(path/'stdout.json'),'stderr':ref(path/'stderr.txt'),'seconds':time.monotonic()-started,'at':rc.stamp()};reference=_quality_immutable(receipt_path,receipt);verify_rapid_call(reference,runtime,image,plan_ref);return receipt['stdout'],reference

def verify_rapid_call(reference,runtime,image,plan_ref):
 receipt=doc(reference);launch=doc(receipt['launch']);expected=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',runtime['python'],'-I','-B',runtime['runner']['path'],'ocr','--manifest',runtime['manifest']['path'],'--manifest-sha',runtime['manifest']['sha256'],'--image',image['path'],'--image-sha',image['sha256'],'--plan',plan_ref['path'],'--plan-sha',plan_ref['sha256']];need(receipt['kind']=='local-RapidOCR-natural-exit-v1'and launch['kind']=='local-RapidOCR-launch-v1'and receipt['argv']==launch['argv']==expected and receipt['runtime']==launch['runtime']==runtime and receipt['image']==launch['image']==image and receipt['plan']==launch['plan']==plan_ref and receipt['returncode']==0 and type(receipt['seconds'])in(int,float)and math.isfinite(receipt['seconds'])and receipt['seconds']>=0,'review-quality-Rapid-natural-exit');raw(receipt['stderr']);output=doc(receipt['stdout']);method(output);provenance=output['provenance'];need(provenance['image']=={'path':image['path'],'sha256':image['sha256']} and provenance['plan']==plan_ref,'review-quality-Rapid-input-provenance');request=doc(plan_ref);need([{'key':c['key'],'box':c['box']}for c in output['cells']]==request['cells'],'review-quality-Rapid-cells-changed');return output

def quality_intent_successor(intent_ref,current_code):
 intent=doc(intent_ref);prior=intent['code'];quality_codes(prior);quality_codes(current_code)
 if prior==current_code:return None
 need(prior[1:]==current_code[1:]and prior[0]['path']==current_code[0]['path'],'review-quality-intent-only-Q-successor')
 import execution_timing as timing
 material=timing.configuration_source_material(prior[0]);dependencies=material['dependencies'];cursor=prior[0]['sha256'];transitions=[]
 for index in range(0,len(dependencies),4):
  link,release,before,after=dependencies[index:index+4];value=doc(release);target=one([t for t in value['targets']if t['target']==prior[0]['path']],'review-quality-intent-successor-slot')
  need(doc(link)=={'kind':'reviewed-configuration-code-successor-link-v1','release':release}and target['before']==before and target['after']==after and target['old_sha256']==cursor==before['sha256'],'review-quality-intent-reviewed-transition')
  transitions.append({'link':link,'release':release,'before':before,'after':after});cursor=after['sha256']
  if cursor==current_code[0]['sha256']:break
 need(transitions and cursor==current_code[0]['sha256'],'review-quality-intent-reviewed-successor')
 base={'kind':'reviewed-Q-saved-preview-intent-successor-v1','original_intent':intent_ref,'prior_code':prior,'current_code':current_code,'business_key_unchanged':True,'original_first_call_reused':True}
 if len(transitions)==1:return {**base,**transitions[0]}
 return {**base,'kind':'reviewed-Q-saved-preview-intent-successor-chain-v1','transitions':transitions}

def refine_saved(preview_ref,out):
 import review_region_capture as region
 m=doc(preview_ref);need(m['state']=='awaiting-visual-review','review-quality-Rapid-awaiting-preview');region.verify(preview_ref['path'],allow_preview=True);p=plan(m);prefix=failed_quality_prefix(preview_ref,Path(out),p);runtime=rapid_runtime();folder=Path(out)/'offline-rapidocr-fallback'/preview_ref['sha256'];final=folder/'quality.json'
 if final.exists():verify_rapid(ref(final),{**m,'state':'complete','quality_approved_at':rc.stamp()});return ref(final)
 intent_path=folder/'intent.json'
 if intent_path.exists():
  intent=doc(ref(intent_path));need(intent['kind']=='saved-preview-local-RapidOCR-intent-v1'and intent['preview']==preview_ref and intent['original_failed_attempt']==prefix and intent['runtime']==runtime ,'review-quality-Rapid-intent-generation')
 else:_quality_immutable(intent_path,{'kind':'saved-preview-local-RapidOCR-intent-v1','preview':preview_ref,'original_failed_attempt':prefix,'runtime':runtime,'code':code(),'created_at':rc.stamp()})
 successor=quality_intent_successor(ref(intent_path),code());successor_ref=_quality_immutable(folder/'source-successors'/(code()[0]['sha256']+'.json'),successor)if successor is not None else None
 started=time.monotonic();first_plan={'cells':[{'key':'single-original-card','box':[0,0,p['image']['width'],p['image']['height']]}]};first_ref,first_call=rapid_call(runtime,p['image'],first_plan,folder/'first');first=doc(first_ref);roi=context_roi(p,first);second_plan={'cells':[{'key':c['key'],'box':c['box']}for c in roi['cells']]};second_ref,second_call=rapid_call(runtime,p['image'],second_plan,folder/'fields-context-v1');checks=evaluate(p,doc(second_ref),roi);raw(preview_ref);raw(p['image']);raw(m['derivation']['source']);failed_quality_prefix(preview_ref,Path(out),p)
 receipt={'kind':'program-review-Rapid-quality-receipt-v1','preview':preview_ref,'image':p['image'],'image_sha256':p['image']['sha256'],'plan':p,'runtime':runtime,'code':code(),'original_failed_attempt':prefix,'intent':ref(intent_path),'first_ocr':first_ref,'first_call':first_call,'roi_method':CONTEXT_ROI_METHOD,'roi':roi,'ocr':second_ref,'second_call':second_call,'pipeline_elapsed_seconds':time.monotonic()-started};receipt.update({'source_generation_continuation':successor_ref}if successor_ref is not None else {});receipt_ref=_quality_immutable(folder/'receipt.json',receipt);a={'kind':KIND,'decision':'finite-card-fields-verified','producer_method':RAPID_METHOD,'registration_preview':preview_ref,'code':code(),'runtime':runtime,'receipt':receipt_ref,'checks':checks,'checked_at':rc.stamp()};reference=_quality_immutable(final,a);verify_rapid(reference,{**m,'state':'complete','quality_approved_at':rc.stamp()});return reference

def verify_rapid(a_ref,m):
 import review_region_capture as region
 a=doc(a_ref);need(a['kind']==KIND and a['decision']=='finite-card-fields-verified'and a['producer_method']==RAPID_METHOD and 'reviewer_role'not in a and 'binary'not in a,'review-quality-Rapid-attestation-kind');preview=doc(a['registration_preview']);expected=copy.deepcopy(m)
 for key in ('quality_attestation','quality_approved_at'):expected.pop(key,None)
 expected['state']='awaiting-visual-review';need(preview==expected,'review-quality-original-preview');region.verify(a['registration_preview']['path'],allow_preview=True);p=plan(preview);receipt=doc(a['receipt']);runtime=rapid_runtime();need(receipt['kind']=='program-review-Rapid-quality-receipt-v1'and a['runtime']==receipt['runtime']==runtime and receipt['preview']==a['registration_preview'] and receipt['image']==p['image']and receipt['image_sha256']==hashlib.sha256(raw(p['image'])).hexdigest()and receipt['plan']==p and receipt['code']==a['code']and quality_codes(a['code']),'review-quality-Rapid-receipt-binding');prefix=failed_quality_prefix(a['registration_preview'],Path(a['registration_preview']['path']).parent/'program-quality',p);intent=doc(receipt['intent']);need(receipt['original_failed_attempt']==prefix==intent['original_failed_attempt']and intent['preview']==a['registration_preview']and intent['runtime']==runtime ,'review-quality-Rapid-failed-prefix-changed');successor=quality_intent_successor(receipt['intent'],a['code']);need((successor is None and 'source_generation_continuation'not in receipt)or(successor is not None and doc(receipt['source_generation_continuation'])==successor),'review-quality-Rapid-intent-successor-changed');first_exit=doc(receipt['first_call']);second_exit=doc(receipt['second_call']);need(first_exit['stdout']==receipt['first_ocr']and second_exit['stdout']==receipt['ocr'],'review-quality-Rapid-raw-receipts');first=verify_rapid_call(receipt['first_call'],runtime,p['image'],first_exit['plan']);need(receipt.get('roi_method')in(None,CONTEXT_ROI_METHOD),'review-quality-Rapid-ROI-method');roi=context_roi(p,first)if receipt.get('roi_method')==CONTEXT_ROI_METHOD else localize(p,first);need(receipt['roi']==roi and doc(second_exit['plan'])=={'cells':[{'key':c['key'],'box':c['box']}for c in roi['cells']]},'review-quality-Rapid-ROI-changed');second=verify_rapid_call(receipt['second_call'],runtime,p['image'],second_exit['plan']);checks=evaluate(p,second,roi);need(a['checks']==checks,'review-quality-Rapid-checks-changed');need(rc.authority.stamp(preview['recorded_at'])<=rc.authority.stamp(a['checked_at'])<=rc.authority.stamp(m['quality_approved_at']),'review-quality-time');return a
