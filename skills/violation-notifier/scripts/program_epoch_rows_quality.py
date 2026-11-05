"""Rows-only source-literal pixels; original epoch history remains unresolved.
No bridge, native capture, approval or registration. Fixed local OCR CLI only.
"""
import copy,datetime,hashlib,json,math,subprocess,time
from pathlib import Path
import program_region_quality as full
import rows_character_range_quality as character
need=full.need;document=full.document;data=full.data;ref=full.ref
KIND='violation-rows-six-source-literals-character-ROI-epoch-unresolved-v2'
METHOD='local-Vision-rows-source-literals-character-ROI-unresolved-epoch-v2'
CAPTION='仅认证本行PNG的通知ID及五列源文字像素；全局DOM epoch变化历史未证实。整改状态由源表/详情链证明，日期表头由独立anchor及完整manifest绑定。'
ATTESTATION_CAPTION='仅认证各源字段完整字面值及完整通知ID；括号仅按显式配对字形比较，额外观测不认证，不声称整列内容完全相等。DOM epoch历史仍未解决；整改由源表/详情/Excel、日期表头由独立anchor及manifest证明。'
FIELDS=('notice_id','reason','subject','object','effective_status','disposal')
def code_refs():return [ref(Path(__file__)),*full.code_refs(),ref(Path(character.__file__)),ref(Path(character.__file__).with_name('rows-range-ocr.swift')),ref(Path(character.__file__).with_name('rows-range-runtime.json'))]
def publish(path,value):
 import region_postguard_retake as pg
 return pg.publish(Path(path).resolve(),value)
def plan(m,source):
 import region_frame_capture as region
 need(m.get('frame_mode')=='rows' and m.get('notice_ids') and not m.get('capture_subcontract'),'epoch-rows-only-full-cell-contract')
 b=m['pinned_inputs'];need(source=={'path':b['source_path'],'sha256':b['source_sha256']} and m['source_sha256']==source['sha256'],'epoch-rows-source-binding')
 consistency=region.postguard.verify_pair(m,business=True)
 need(consistency is not None and consistency.get('contract')=='unresolved-global-epoch-change-v1' and all(consistency.get(k)is False for k in ('automatic_certification','semantic_or_layout_history_resolved','outside_scope_cause_proven')),'epoch-rows-original-unresolved-required')
 # Only a copy supplies unchanged layout to the old pixel planner. This is never
 # written into original preview/proofs or represented as history verification.
 layout=copy.deepcopy(m);layout['public_dom_proof']['after']=copy.deepcopy(layout['public_dom_proof']['before']);layout.pop('postguard_consistency')
 p=full.plan(layout);need(p['frame_mode']=='rows' and len(p['cells'])==5*len(m['notice_ids']),'epoch-rows-five-cells-per-notice')
 src=document(source);records={r['notice_id']:r for r in src['records']['rows']};need(len(records)==len(src['records']['rows']),'epoch-rows-duplicate-source-ID');contracts=[]
 observation=document({'path':b['observation_path'],'sha256':b['observation_sha256']})
 def walk(n):
  yield n
  for child in n.get('children',[]):yield from walk(child)
 tree=list(walk(observation['tree']['root']))
 for notice in m['notice_ids']:
  elements=[e for e in b['command']['elements']if e['kind']=='row'and e['notice_id']==notice];need(len(elements)==1,'epoch-rows-one-source-row-command');expected=json.loads(elements[0]['expected_text']);cells=[c for c in p['cells']if c['key'].split(':')[0]==notice]
  need(notice in records and expected==[notice,*[c['expected']for c in cells]] and [c['key']for c in cells]==[notice+':'+f for f in full.FIELDS] and cells[0]['expected'].count(notice)==1,'epoch-rows-original-six-value-contract')
  need(all(a['box'][0]<b['box'][0] and a['box'][2]<b['box'][2] for a,b in zip(cells,cells[1:])) and max(c['box'][1] for c in cells)<min(c['box'][3] for c in cells),'epoch-rows-five-column-order-baseline')
  record=records[notice];proof_cells=[c for row in m['public_dom_proof']['before']['base_proof']['business_cells']if row['notice_id']==notice for c in row['cells']]
  for field,text in (('reason',record['reason']),('subject',record['subject']),('object',record['object_name']),('object',record['object_type'])):
   cell=next(c for c in proof_cells if c['field']==field);nodes=[n for n in tree if n.get('selector')==cell['selector']];need(len(nodes)==1,'epoch-rows-source-cell-selector');leaves=[n for n in walk(nodes[0])if n.get('name','').strip()and not any(x.get('name','').strip()for child in n.get('children',[])for x in walk(child))];need(len([n for n in leaves if n['name']==text and n['selector']in cell['text_selectors']])==1,'epoch-rows-source-semantic-leaf')
  need(expected[4]==record['effectiveness_status']and full.compact(expected[5])==full.compact(' '.join(record['actions'])),'epoch-rows-source-action-state')
  contracts.append({'notice_id':notice,'original_six_values':expected,'cell_keys':[c['key']for c in cells],'rectification_source_only':records[notice]['rectification_status']})
 for c in p['cells']:
  x,y,r,d=c['box'];need(0<=x<r<=p['image']['width']and 0<=y<d<=p['image']['height'],'epoch-rows-bounded-cell-required')
 scope={k:src[k]for k in ('company','groupid','start','end_exclusive')}
 need(all(str(m['page_scope'][k])==str(v)for k,v in scope.items()),'epoch-rows-original-scope-conflict')
 return {**p,'kind':'program-rows-epoch-pixel-plan-v1','row_contracts':contracts,'source_scope':scope,'postguard_consistency':copy.deepcopy(consistency),'history_resolved':False,'automatic_history_certification':False,'rectification_pixel_certified':False,'date_header_pixel_certified':False,'caption':CAPTION}
def _whole_cell_evaluate(p,ocr):
 checks=full.evaluate(p,ocr)
 # Original fixed runtime crops each real bounded cell before recognition.
 # Preserve full.evaluate's <=1px Vision box-estimator tolerance; this certifies
 # source text, not glyph coordinates or any pixels beyond the actual input.
 bykey={c['key']:c for c in checks};rows=[]
 for row in p['row_contracts']:
  notice=row['notice_id'];reason=bykey[notice+':reason']['observed_text'];need(reason.count(notice)==1,'epoch-rows-full-notice-ID-required')
  rows.append({'notice_id':notice,'notice_id_pixel_certified':True,'certified_fields':list(FIELDS),'cell_checks':[bykey[k]for k in row['cell_keys']],'rectification':{'source_value':row['rectification_source_only'],'pixel_certified':False,'basis':'original-source-detail-Excel-chain'}})
 return {'kind':'rows-six-source-value-pixels-history-unresolved-v1','rows':rows,'scope':{'source_verified':p['source_scope'],'pixel_certified':False},'history_resolved':False,'automatic_history_certification':False,'rectification_pixel_certified':False,'date_header_pixel_certified':False,'date_header_basis':'separate-original-anchor-and-complete-manifest','all_fields_visible_claimed':False,'caption':CAPTION}
def verify_stage(exitref,binary,stdout,*,expected_plan):
 e=document(exitref);dispatch=document(e['dispatch']);p=document(e['plan']);need(p==expected_plan,'epoch-rows-exit-plan-conflict');argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',binary['path'],p['image']['path'],e['plan']['path']]
 need(e.get('kind')=='rows-epoch-OCR-natural-exit-v1'and type(e.get('returncode'))is int and e['returncode']==0 and e['argv']==argv and e['binary']==binary and e['stdout']==stdout and e['PID_available']is False,'epoch-rows-natural-exit-binding')
 need(dispatch=={'kind':'rows-epoch-OCR-dispatch-intent-v1','argv':argv,'binary':binary,'plan':e['plan'],'started_at':e['started_at'],'started_monotonic':e['started_monotonic'],'PID_available':False},'epoch-rows-dispatch-binding')
 need(all(type(e[k])in(int,float)and math.isfinite(e[k])for k in ('started_monotonic','exited_monotonic','elapsed_seconds'))and e['exited_monotonic']>=e['started_monotonic']and e['elapsed_seconds']==e['exited_monotonic']-e['started_monotonic']and datetime.datetime.fromisoformat(e['started_at'])<=datetime.datetime.fromisoformat(e['exited_at']),'epoch-rows-stage-time')
 for r in (e['dispatch'],e['plan'],e['stdout'],e['stderr'],binary):data(r)
 return e
def run_stage(out,binary,planref):
 import region_frame_capture as region
 need(not any((out/name).exists()for name in ('ocr-dispatch.json','ocr-exit.json','ocr-timeout.json','ocr.json','ocr.stderr')),'epoch-rows-existing-stage-no-reOCR')
 p=document(planref);argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',binary['path'],p['image']['path'],planref['path']];start=time.monotonic();at=region.stamp();dispatch=publish(out/'ocr-dispatch.json',{'kind':'rows-epoch-OCR-dispatch-intent-v1','argv':argv,'binary':binary,'plan':planref,'started_at':at,'started_monotonic':start,'PID_available':False})
 try:run=subprocess.run(argv,capture_output=True,timeout=60)
 except subprocess.TimeoutExpired as error:
  stdout=publish(out/'ocr.json',error.stdout or b'');stderr=publish(out/'ocr.stderr',error.stderr or b'');end=time.monotonic();publish(out/'ocr-timeout.json',{'kind':'rows-epoch-OCR-timeout-v1','dispatch':dispatch,'stdout':stdout,'stderr':stderr,'elapsed_seconds':end-start,'natural_exit_observed':False});raise
 stdout=publish(out/'ocr.json',run.stdout);stderr=publish(out/'ocr.stderr',run.stderr);end=time.monotonic();exitref=publish(out/'ocr-exit.json',{'kind':'rows-epoch-OCR-natural-exit-v1','dispatch':dispatch,'argv':argv,'binary':binary,'plan':planref,'started_at':at,'started_monotonic':start,'exited_at':region.stamp(),'exited_monotonic':end,'elapsed_seconds':end-start,'PID_available':False,'returncode':run.returncode,'stdout':stdout,'stderr':stderr});need(run.returncode==0,'epoch-rows-OCR-process-failed');verify_stage(exitref,binary,stdout,expected_plan=p);return stdout,exitref

def runtime_refs():return {'first':full.runtime(),'locator':character.runtime('locator'),'second':character.runtime('second')}
def evaluate(p,first,locator=None,second=None):return character.evaluate(p,first,locator,second)
def fallback(p,first,out):
 lp=character.plan(p,document(first))
 if not lp['cells']:return None
 lpr=publish(out/'locator-plan.json',lp);lr,le=character.run_stage(out,'locator',character.runtime('locator'),lpr);rp=character.ROI(lp,document(lr));rpr=publish(out/'second-plan.json',rp);sr,se=character.run_stage(out,'second',character.runtime('second'),rpr)
 return {'locator_plan':lpr,'locator':lr,'locator_exit':le,'second_plan':rpr,'second':sr,'second_exit':se}
def verify_fallback(p,first,fb,*,reviewed_locator_binary=None):
 lp=character.plan(p,document(first))
 if not lp['cells']:
  need(fb is None,'rows-character-unneeded-fallback');return evaluate(p,document(first))
 need(isinstance(fb,dict)and set(fb)=={'locator_plan','locator','locator_exit','second_plan','second','second_exit'},'rows-character-fallback-fields');need(document(fb['locator_plan'])==lp,'rows-character-locator-plan');le=document(fb['locator_exit']);need(le['stdout']==fb['locator'],'rows-character-locator-stdout');character.verify_stage(fb['locator_exit'],'locator',le['binary'],fb['locator_plan'],lp,reviewed_binary=reviewed_locator_binary);rp=character.ROI(lp,document(fb['locator']));need(document(fb['second_plan'])==rp,'rows-character-second-plan');se=document(fb['second_exit']);need(se['stdout']==fb['second'],'rows-character-second-stdout');character.verify_stage(fb['second_exit'],'second',full.runtime(),fb['second_plan'],rp)
 return evaluate(p,document(first),document(fb['locator']),document(fb['second']))
def cached_evidence(release_ref,preview_ref,source,p):
 import violation_reboot_continuation as recovery
 release=document(release_ref);need(recovery.rows_character_range_cache_authority(release_ref)==release.get('rows_character_range_cached_evaluation'),'rows-character-canonical-Root-authority');need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director','rows-character-reviewed-cache-release')
 targets=release['targets'];need(len({t['target']for t in targets})==len(targets),'rows-character-duplicate-release-target');current=code_refs()
 for r in(current[0],ref(Path(character.__file__))):need(len([t for t in targets if t['target']==r['path']and t['after']['sha256']==r['sha256']])==1,'rows-character-current-module-release-pin')
 a=release['rows_character_range_cached_evaluation'];keys={'kind','preview','source','first_plan','first','first_exit','evaluation_result','evaluation_summary','evaluation_freeze','evaluation_script','evaluation_module','original_freeze','original_module','locator_runtime'}
 need(set(a)==keys and a['kind']=='root-pinned-original-rows-character-ROI-cache-v1'and a['preview']==preview_ref and a['source']==source,'rows-character-exact-cache-authority')
 for k in keys-{'kind','locator_runtime'}:data(a[k])
 freeze=document(a['evaluation_freeze']);need(freeze['kind']=='isolated-zero-dispatch-character-ROI-fix-freeze-v2'and freeze['module']==a['evaluation_module']and freeze['entry']==a['evaluation_script']and freeze['original_freeze']==a['original_freeze'],'rows-character-evaluation-freeze')
 for r in freeze['files']:data(r)
 original=document(a['original_freeze']);need(original['module']==a['original_module'],'rows-character-original-freeze-module');data(a['original_module'])
 summary=document(a['evaluation_summary']);v=document(a['evaluation_result']);need(summary['kind']=='rows-character-range-evaluation-v2-pixels-only-success-v1'and summary['result']==a['evaluation_result']and summary['original_pins_unchanged']is True and summary['no_attest_approve_accept']is True,'rows-character-cached-summary')
 exit0=document(summary['outer_exit']);need(exit0['returncode']==0 and exit0['argv']==[exit0['argv'][0],a['evaluation_script']['path']],'rows-character-cached-natural-worker');data(exit0['stdout']);data(exit0['stderr']);data(exit0['started'])
 need(v['kind']=='fixed-original-character-ROI-continuation-result-v1'and v['status']=='pixel-pass-not-business-approved'and all(v.get(k)is False for k in('attestation_generated','approved','accepted','history_resolved')),'rows-character-cached-pixel-result')
 continuation=document(v['continuation']);need(continuation['module']==a['evaluation_module']and continuation['input_refs']==[preview_ref,source,a['first_plan'],a['first'],a['first_exit']],'rows-character-original-input-refs');need(document(a['first_plan'])==p,'rows-character-cached-original-plan');verify_stage(a['first_exit'],full.runtime(),a['first'],expected_plan=p)
 lr=a['locator_runtime'];need(set(lr)=={'binary','swift','manifest'}and lr['binary']==continuation['locator_runtime']and lr['binary']['sha256']==character.runtime('locator')['sha256'],'rows-character-reviewed-runtime-alias')
 for name in('swift','manifest'):
  expected=ref(Path(character.__file__).with_name('rows-range-ocr.swift'if name=='swift'else'rows-range-runtime.json'));need(lr[name]['sha256']==expected['sha256']and data(lr[name])==data(expected),'rows-character-reviewed-runtime-material')
 data(lr['binary']);le=document(v['locator_exit']);se=document(v['second_exit']);need(le==summary['stages']['locator']and se==summary['stages']['second'],'rows-character-natural-stages-summary');fb={'locator_plan':le['plan'],'locator':v['locator'],'locator_exit':v['locator_exit'],'second_plan':se['plan'],'second':v['second'],'second_exit':v['second_exit']};checks=verify_fallback(p,a['first'],fb,reviewed_locator_binary=lr['binary']);need(checks==v['checks']==summary['checks'],'rows-character-cached-all-checks')
 return a['first'],a['first_exit'],fb,checks

def verify(attestation,m,source):
 import region_frame_capture as region
 a=document(attestation);need(a.get('kind')==KIND and a.get('producer_method')==METHOD and a.get('decision')=='six-source-literals-verified-history-unresolved'and 'reviewer_role'not in a and a.get('history_resolved')is False and a.get('whole_cell_exact_claimed')is False,'rows-character-attestation-contract')
 preview=document(a['registration_preview']);expected=copy.deepcopy(m)
 for k in('quality_attestation','quality_approved_at'):expected.pop(k,None)
 expected['state']='awaiting-visual-review';need(preview==expected,'quality-original-preview-conflict');region.validate_frame(preview['image']['path'],preview,source=source,allow_preview=True)
 need(a['source']==source and a['code']==code_refs()and a['runtimes']==runtime_refs(),'rows-character-code-source-runtime');r=document(a['receipt']);p=plan(preview,source);need(r['kind']=='program-rows-character-ROI-pixel-receipt-v2'and r['preview']==a['registration_preview']and r['plan']==p and r['code']==a['code']and r['runtimes']==a['runtimes']and r['cell_pixels']==full.pixel_refs(p),'rows-character-receipt-binding')
 if r['cached_release']is not None:
  first,first_exit,fb,checks=cached_evidence(r['cached_release'],a['registration_preview'],source,p);need((first,first_exit,fb)==(r['first'],r['first_exit'],r['fallback']),'rows-character-cached-receipt')
 else:
  verify_stage(r['first_exit'],full.runtime(),r['first'],expected_plan=p);checks=verify_fallback(p,r['first'],r['fallback'])
 need(a['checks']==checks and a['caption']==ATTESTATION_CAPTION,'rows-character-complete-source-checks');need(region.sr.when(preview['recorded_at'])<=region.sr.when(a['checked_at'])<=region.sr.when(m['quality_approved_at']),'quality-program-time')
 for x in(a['registration_preview'],a['receipt'],r['first'],r['first_exit'],*a['code'],*a['runtimes'].values()):data(x)
 return a

def create(preview_ref,source,outdir,*,cached_release=None):
 import region_frame_capture as region
 m=document(preview_ref);need(m.get('state')=='awaiting-visual-review','quality-original-preview-required');region.validate_frame(m['image']['path'],m,source=source,allow_preview=True);p=plan(m,source);code=code_refs();runtimes=runtime_refs();out=Path(outdir).resolve();final=out/'quality.json'
 if out.exists():
  need(final.exists(),'rows-character-existing-attempt-no-new-OCR');verify(ref(final),{**m,'state':'complete','quality_approved_at':region.stamp()},source);return ref(final)
 out.mkdir(parents=True,exist_ok=False);publish(out/'intent.json',{'kind':'program-rows-character-ROI-quality-intent-v2','preview':preview_ref,'source':source,'code':code,'runtimes':runtimes,'cached_release':cached_release,'started_at':region.stamp()});started=time.monotonic()
 try:
  publish(out/'plan.json',p)
  if cached_release is not None:first,first_exit,fb,checks=cached_evidence(cached_release,preview_ref,source,p)
  else:first,first_exit=run_stage(out,full.runtime(),ref(out/'plan.json'));fb=fallback(p,first,out);checks=verify_fallback(p,first,fb)
  receipt=publish(out/'receipt.json',{'kind':'program-rows-character-ROI-pixel-receipt-v2','preview':preview_ref,'plan':p,'code':code,'runtimes':runtimes,'cell_pixels':full.pixel_refs(p),'first':first,'first_exit':first_exit,'fallback':fb,'cached_release':cached_release,'pipeline_elapsed_seconds':time.monotonic()-started});region.validate_frame(m['image']['path'],m,source=source,allow_preview=True);need(code==code_refs()and runtimes==runtime_refs(),'rows-character-code-runtime-changed')
  for x in(preview_ref,source,m['image'],m['derivation']['source']):data(x)
  return publish(final,{'kind':KIND,'producer_method':METHOD,'decision':'six-source-literals-verified-history-unresolved','registration_preview':preview_ref,'source':source,'code':code,'runtimes':runtimes,'receipt':receipt,'checks':checks,'history_resolved':False,'whole_cell_exact_claimed':False,'caption':ATTESTATION_CAPTION,'checked_at':region.stamp()})
 except Exception as error:publish(out/'failure.json',{'kind':'program-rows-character-ROI-quality-failure-v2','preview':preview_ref,'source':source,'reason':str(error),'elapsed_seconds':time.monotonic()-started});raise
