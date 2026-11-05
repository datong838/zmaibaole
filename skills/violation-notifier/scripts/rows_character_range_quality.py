"""Independent rows literal-range locator/ROI evidence; no approval or capture.
Old whole-cell OCR/cache is immutable. No function below issues UI or changes it.
The locator source strings are used AFTER recognition, never as Vision hints.
"""
import copy,datetime,hashlib,json,math,re,subprocess,time
from pathlib import Path
KIND='rows-six-source-fields-character-ROI-pixels-history-unresolved-v1'
RUNTIME_PIN={'kind': 'local-rows-character-range-runtime-v1', 'swift_sha256': '43bb3d9c3ea8c816e4f33c518544517a8257abce9ef292c3dbf541714ddbedff', 'binary_sha256': '90619dab3871b9cbee348b0754109000c3e473ab7d0bbe1b3168de073b0b97ed'}
def need(v,reason):
 if not v:raise ValueError(reason)
def compact(s):return ''.join(s.split())
def equal_text(a,b):return compact(a)==compact(b)and re.findall(r"[A-Za-z0-9]+(?:\.[0-9]+)?",a)==re.findall(r"[A-Za-z0-9]+(?:\.[0-9]+)?",b)
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def digest(v):return hashlib.sha256(canonical(v)).hexdigest()
def ref(p):p=Path(p).resolve();return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def raw(r):
 p=Path(r['path']);need(p.is_absolute()and p.resolve()==p and not any(x.is_symlink()for x in(p,*p.parents)),'range-canonical-ref');v=p.read_bytes();need(hashlib.sha256(v).hexdigest()==r['sha256'],'range-reference-changed');return v
def doc(r):return json.loads(raw(r))
def publish(p,v):
 p=Path(p);b=v if isinstance(v,bytes)else canonical(v)
 try:
  with p.open('xb')as f:f.write(b);f.flush();__import__('os').fsync(f.fileno())
 except FileExistsError:need(p.read_bytes()==b,'range-immutable-conflict')
 return ref(p)
def claim_intent(p,v):
 # Unlike immutable evidence publishing, a dispatch claim can NEVER be reused,
 # even when another process wrote identical bytes.
 with Path(p).open('xb')as f:f.write(canonical(v));f.flush();__import__('os').fsync(f.fileno())
 return ref(p)
def orthography(text):
 # Only paired ASCII/fullwidth parenthesis glyphs. No NFKC, letters or numbers.
 stack=[]
 for c in text:
  if c in '(（':stack.append(c)
  elif c in ')）':need(stack and (stack.pop(),c)in(('(',')'),('（','）')),'range-unpaired-parentheses')
 need(not stack,'range-unpaired-parentheses');return text.translate(str.maketrans({'（':'(', '）':')'}))
def method(ocr,kind='local-vision-cell-ocr-v1'):
 need(ocr.get('kind')==kind and ocr.get('recognition_level')=='accurate'and ocr.get('recognition_languages')==['zh-Hans','en-US']and ocr.get('language_correction')is False and ocr.get('CPU_only')is True,'range-OCR-method');need(type(ocr.get('elapsed_seconds'))in(int,float)and math.isfinite(ocr['elapsed_seconds'])and ocr['elapsed_seconds']>=0,'range-OCR-time')
def bounds(b,w,h,tolerance=0):
 need(isinstance(b,list)and len(b)==4 and all(type(v)in(int,float)and math.isfinite(v)for v in b)and b[2]>0 and b[3]>0 and b[0]>=-tolerance/w and b[1]>=-tolerance/h and b[0]+b[2]<=1+tolerance/w and b[1]+b[3]<=1+tolerance/h,'range-estimate-outside-input')
def ordered(rows):return sorted(rows,key=lambda r:(-round(r['box'][1]+r['box'][3]/2,2),r['box'][0]))
def checked_rows(cell):
 w,h=cell['box'][2]-cell['box'][0],cell['box'][3]-cell['box'][1]
 for r in cell['observations']:
  need(set(r)=={'text','confidence','box'}and isinstance(r['text'],str)and r['text']and type(r['confidence'])in(int,float)and math.isfinite(r['confidence'])and .5<=r['confidence']<=1,'range-first-uncertain');bounds(r['box'],w,h,1)
 return cell['observations']
def occurrences(literal,text):
 # No internal digit joining, numeric/letter normalization or prefix matching.
 return [m for m in re.finditer(re.escape(literal),text)if(m.start()==0 or not text[m.start()-1].isalnum())and(m.end()==len(text)or not text[m.end()].isalnum())]
def plan(row_plan,first):
 method(first);contracts=row_plan['row_contracts'];need(contracts and len({r['notice_id']for r in contracts})==len(contracts)and len(row_plan['cells'])==len(first['cells'])==5*len(contracts),'range-original-finite-five-cells-per-row');fields=('reason','subject','object','effective_status','disposal')
 for index,row in enumerate(contracts):
  cells=row_plan['cells'][5*index:5*(index+1)];need([c['key']for c in cells]==[row['notice_id']+':'+f for f in fields]and row['cell_keys']==[c['key']for c in cells]and row['original_six_values']==[row['notice_id'],*[c['expected']for c in cells]],'range-original-six-source-values-order')
 result=[];facts=[]
 for c,o in zip(row_plan['cells'],first['cells']):
  need(o['key']==c['key']and o['box']==c['box']and set(o)=={'key','box','observations'},'range-first-cell-binding');rows=checked_rows(o);seen=' '.join(x['text']for x in ordered(rows));notice,field=c['key'].rsplit(':',1)
  lhs,rhs=(orthography(c['expected']),orthography(seen))if field=='subject'else(c['expected'],seen)
  if equal_text(lhs,rhs):facts.append({'key':c['key'],'source_literal':c['expected'],'observations':copy.deepcopy(rows),'comparison':'paired-parentheses-only'if field=='subject'and lhs!=c['expected']or field=='subject'and rhs!=seen else'exact-whitespace','pixel_scope':'source-literal-only'});continue
  need(field in('reason','object'),'range-no-supported-literal-fallback')
  if field=='reason':
   m=re.fullmatch(r'(.*?)\s+(ID:\s*'+re.escape(notice)+r')',c['expected']);need(m,'range-reason-ID-source');prefix,literal=m.groups()
  else:
   m=re.fullmatch(r'(.*?)\s+([0-9]+)',c['expected']);need(m,'range-object-ID-source');prefix,literal=m.groups()
  owners=[(i,r)for i,r in enumerate(rows)if len(occurrences(literal,r['text']))==1];need(len(owners)==1 and sum(len(occurrences(literal,r['text']))for r in rows)==1,'range-first-full-literal-not-unique');owner_index,owner=owners[0]
  # All other source content must already be exact, not merely a substring.
  other=' '.join(r['text']for r in ordered([r for i,r in enumerate(rows)if i!=owner_index]));need(equal_text(other,prefix),'range-other-source-content-not-exact')
  result.append({'key':c['key'],'box':c['box'],'queries':{'source_token':literal},'original_expected':c['expected'],'expected_prefix':prefix,'first_owner_index':owner_index,'first_owner':copy.deepcopy(owner),'other_source_observations':copy.deepcopy([r for i,r in enumerate(rows)if i!=owner_index])})
 need(all(len([c for c in result if c['key'].rsplit(':',1)[0]==r['notice_id']])<=2 for r in contracts)and len(result)<=2*len(contracts),'range-fallback-at-most-two-ID-fields-per-row');return {'kind':'rows-source-token-character-locator-plan-v1','image':row_plan['image'],'cells':result,'parent_plan_sha256':digest(row_plan),'first_sha256':digest(first),'certified_cached_source_literals':facts,'history_resolved':False,'rectification_pixel_certified':False,'date_header_pixel_certified':False,'whole_cell_exact_claimed':False}
def ROI(locator_plan,locator):
 method(locator,'local-vision-rows-character-range-v1');need(len(locator['cells'])==len(locator_plan['cells']),'range-locator-cell-count');result=[]
 for c,o in zip(locator_plan['cells'],locator['cells']):
  need(set(o)=={'key','box','observations','ranges'}and o['key']==c['key']and o['box']==c['box'],'range-locator-cell-binding');literal=c['queries']['source_token'];w,h=c['box'][2]-c['box'][0],c['box'][3]-c['box'][1];owners=[(i,r,m)for i,r in enumerate(o['observations'])for m in occurrences(literal,r['text'])];need(len(owners)==1,'range-locator-owner-not-unique');index,owner,match=owners[0];need(len(o['ranges'])==1,'range-locator-range-not-unique');r=o['ranges'][0]
  need(set(r)=={'field','text','owner_index','UTF16_range','box','confidence'}and r['field']=='source_token'and r['text']==literal and r['owner_index']==index,'range-locator-range-owner-binding')
  need(r['UTF16_range']==[len(owner['text'][:match.start()].encode('utf-16-le'))//2,len(literal.encode('utf-16-le'))//2],'range-locator-character-offset');need(type(r['confidence'])in(int,float)and math.isfinite(r['confidence'])and 0<=r['confidence']<=1 and r['confidence']==owner['confidence'],'range-locator-confidence-binding');bounds(r['box'],w,h,1);bounds(owner['box'],w,h,1)
  x,y,bw,bh=r['box'];ox,oy,ow,oh=owner['box'];need(x>=ox-1/w and y>=oy-1/h and x+bw<=ox+ow+1/w and y+bh<=oy+oh+1/h,'range-locator-range-outside-owner')
  left=c['box'][0]+x*w;top=c['box'][1]+(1-y-bh)*h;right=c['box'][0]+(x+bw)*w;bottom=c['box'][1]+(1-y)*h
  box=[max(c['box'][0],math.floor(left)-2),max(c['box'][1],math.floor(top)-2),min(c['box'][2],math.ceil(right)+2),min(c['box'][3],math.ceil(bottom)+2)]
  need(0<=box[0]<box[2]<=locator_plan['image']['width']and 0<=box[1]<box[3]<=locator_plan['image']['height'],'range-real-ROI-outside-PNG')
  result.append({'key':c['key'],'box':box,'expected':literal,'locator_range':copy.deepcopy(r),'locator_owner':copy.deepcopy(owner),'unverified_extra_text':owner['text'][:match.start()]+owner['text'][match.end():],'all_locator_observations':copy.deepcopy(o['observations']),'padding_pixels':2,'estimate_tolerance_pixels':1})
 return {'kind':'rows-independent-source-token-ROI-plan-v1','image':locator_plan['image'],'cells':result,'locator_plan_sha256':digest(locator_plan),'locator_result_sha256':digest(locator),'history_resolved':False,'whole_cell_exact_claimed':False}
def evaluate(row_plan,first,locator,second):
 lp=plan(row_plan,first);checks=[]
 if not lp['cells']:need(locator is None and second is None,'range-no-unneeded-fallback')
 else:
  rp=ROI(lp,locator);method(second);need(len(second['cells'])==len(rp['cells']),'range-second-count')
  for c,o in zip(rp['cells'],second['cells']):
   need(set(o)=={'key','box','observations'}and o['key']==c['key']and o['box']==c['box'],'range-second-cell-binding');rows=checked_rows(o);text=' '.join(r['text']for r in ordered(rows));need(equal_text(text,c['expected']),'range-independent-literal-not-exact');need(len(occurrences(c['expected'],text))==1,'range-independent-complete-ID-boundary');checks.append({'key':c['key'],'source_literal':c['expected'],'observed_text':text,'observations':copy.deepcopy(rows),'unverified_locator_extra_text':c['unverified_extra_text']})
 return {'kind':KIND,'cached_source_literal_checks':lp['certified_cached_source_literals'],'independent_ID_checks':checks,'original_first_OCR':copy.deepcopy(first),'locator_evidence':copy.deepcopy(locator),'history_resolved':False,'rectification_pixel_certified':False,'date_header_pixel_certified':False,'whole_cell_exact_claimed':False,'source_fields_complete':len(lp['certified_cached_source_literals'])+len(checks)==len(row_plan['cells']),'certified_source_fields':['notice_id','reason','subject','object','effective_status','disposal']}

def runtime(stage):
 need(stage in('locator','second'),'range-stage-kind')
 if stage=='second':
  import program_region_quality as original
  return original.runtime()
 d=Path(__file__).resolve().parent;v=doc(ref(d/'rows-range-runtime.json'));need(v==RUNTIME_PIN and ref(d/'rows-range-ocr.swift')['sha256']==v['swift_sha256']and ref(d/'rows-range-ocr')['sha256']==v['binary_sha256'],'range-fixed-locator-runtime');return ref(d/'rows-range-ocr')
def run_stage(out,stage,binary,planref):
 need(stage in('locator','second')and binary==runtime(stage),'range-stage-runtime');out=Path(out);need(out.is_dir(),'range-existing-output-required');intent=out/(stage+'-intent.json');need(not any((out/(stage+suffix)).exists()for suffix in('-intent.json','-stdout.json','-stderr.log','-exit.json','-timeout.json')),'range-existing-stage-no-repeat');need({p.name for p in out.glob(stage+'-*')}<={stage+'-plan.json'},'range-unknown-stage-artifact');p=doc(planref);existing_plan=out/(stage+'-plan.json');need(not existing_plan.exists()or ref(existing_plan)==planref,'range-existing-plan-conflict');raw(binary);argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',binary['path'],p['image']['path'],planref['path']];start=time.monotonic();started=datetime.datetime.now(datetime.timezone.utc).isoformat();ir=claim_intent(intent,{'kind':'rows-character-ROI-stage-intent-v1','stage':stage,'plan':planref,'binary':binary,'argv':argv,'started_at':started,'started_monotonic':start,'PID_available':False})
 try:v=subprocess.run(argv,capture_output=True,timeout=60)
 except subprocess.TimeoutExpired as e:
  stdout=publish(out/(stage+'-stdout.json'),e.stdout or b'');stderr=publish(out/(stage+'-stderr.log'),e.stderr or b'');publish(out/(stage+'-timeout.json'),{'intent':ir,'stdout':stdout,'stderr':stderr,'elapsed_seconds':time.monotonic()-start,'natural_exit_observed':False});raise
 stdout=publish(out/(stage+'-stdout.json'),v.stdout);stderr=publish(out/(stage+'-stderr.log'),v.stderr);end=time.monotonic();er=publish(out/(stage+'-exit.json'),{'kind':'rows-character-ROI-natural-exit-v1','intent':ir,'plan':planref,'binary':binary,'argv':argv,'stdout':stdout,'stderr':stderr,'returncode':v.returncode,'exited_monotonic':end,'elapsed_seconds':end-start,'exited_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'PID_available':False});need(type(v.returncode)is int and v.returncode==0,'range-stage-process-failed');verify_stage(er,stage,binary,planref,p);return stdout,er

def verify_stage(exitref,stage,binary,planref,expected_plan,*,reviewed_binary=None):
 need(stage in('locator','second'),'range-stage-kind');current=runtime(stage);need(binary==current or(reviewed_binary==binary and binary['sha256']==current['sha256']and raw(binary)==raw(current)),'range-stage-runtime');e=doc(exitref);i=doc(e['intent']);p=doc(planref);need(p==expected_plan and e['plan']==planref and p['image']==expected_plan['image'],'range-stage-exact-plan-image');argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',binary['path'],p['image']['path'],planref['path']]
 need(e['kind']=='rows-character-ROI-natural-exit-v1'and type(e['returncode'])is int and e['returncode']==0 and e['binary']==binary and e['argv']==argv and e['PID_available']is False,'range-stage-exit-binding')
 need(i=={'kind':'rows-character-ROI-stage-intent-v1','stage':stage,'plan':planref,'binary':binary,'argv':argv,'started_at':i['started_at'],'started_monotonic':i['started_monotonic'],'PID_available':False},'range-stage-intent-binding')
 need(all(type(x)in(int,float)and math.isfinite(x)for x in(i['started_monotonic'],e['exited_monotonic']))and type(e['elapsed_seconds'])in(int,float)and math.isfinite(e['elapsed_seconds'])and e['exited_monotonic']>=i['started_monotonic']and e['elapsed_seconds']==e['exited_monotonic']-i['started_monotonic']and datetime.datetime.fromisoformat(e['exited_at'])>=datetime.datetime.fromisoformat(i['started_at']),'range-stage-time')
 for r in(e['intent'],planref,binary,e['stdout'],e['stderr'],p['image']):raw(r)
 return e
