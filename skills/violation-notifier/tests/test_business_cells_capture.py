"""Actual saved source/DOM, synthetic public geometry/SCK. Never UI/live acceptance."""
import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'skills/violation-notifier/scripts'))
import prepare_records_profile as profile_api
import region_frame_capture as r
import business_cells_capture as b
BASE=ROOT/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
transport=load('business_fake_transport',ROOT/'skills/chrome-dom-export/tests/test_native_window_capture.py')
class BusinessCells(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.source=profile_api.d.ref(BASE/'complete-governance-source.json');cls.job=profile_api.d.ref(BASE/'navigation-job.json');cls.query=profile_api.d.ref(BASE/'records-range-query-v9.json');cls.q=profile_api.d.document(cls.query)
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.src=self.write('source.json',profile_api.d.document(self.source));self.profile=profile_api.derive(self.src,self.job,self.query,full_source_check=False,evidence_contract=b.CONTRACT);self.pr=self.write('profile.json',self.profile);self.nav_folder=self.root/'.records-region-navigation'/self.src['sha256'];self.nav_folder.mkdir(parents=True);meta=self.profile['derivation'];self.nav_file=self.nav_folder/'state.json';r.atomic(self.nav_file,{'binding':{'schema':'records-region-navigation-v1','source':self.src,'profile':self.pr,'job':meta['job'],'query':meta['query'],'tab_id':meta['tab_id'],'window_id':meta['window_id']},'operations':[]});self.page=1;self.ellipsis=True;self.captured=0;self.paths=[]
  self.native=transport.FakeNative();self.native.items[0]['kCGWindowBounds']={'X':0,'Y':30,'Width':1440,'Height':850}
  def capture(cg,out):self.captured+=1;r.region.pillow().new('RGB',(2880,1700),(17,23,42)).save(out);return {'width':2880,'height':1700}
  self.native.capture=capture;self.ax=type('AX',(),{'observe':lambda _,scope:{'pid':55,'url':scope['url'],'AX_main_window':{'x':0,'y':30,'width':1440,'height':850},'AX_webarea':{'x':0,'y':117,'width':1440,'height':763},'webarea_contents_read':False,'geometry_purpose':'evidence-crop-only','input_actions_used':False}})()
 def write(self,name,value):p=self.root/name;profile_api.d.exclusive(p,value);return profile_api.d.ref(p)
 def inputs(self):return r.fc.page_inputs(self.src,self.q['pages'][self.page-1]['observation'],self.pr)
 def geometry(self):return dict(rendered=True,box_viewport_contained=True,unsupported_css_absent=True,text_unclipped=True,ellipsis_supported=True,text_clips=[],evidence_eligible=True,preview_required=False,occlusion_verified=False)
 def base(self,i):
  c=i['command'];s=i['business_spec'];out={'source':'local-dom-bridge','method':'public-DOM-semantic-viewport-proof','source_sha256':c['source_sha256'],'dom_sha256':c['dom_sha256'],'epoch':self.page,'url':i['url'],'viewport_only':True,'pixel_coordinates_returned':False,'pixel_actions_used':False,'all_fully_visible':False,'scope':{k:c[k] for k in ('tabId','windowId','groupid')},'safety_version':'dom-only-20261021-11','hash_contract':'gov-records-stable5-v1','hash_scope':'versioned-public-DOM-projection','evidence_contract':b.CONTRACT,'diagnostic_build':'viewport-notice-business-cells-v3','elements':[{**{k:e[k] for k in ('key','kind','notice_id','locator')},'text':e['expected_text'],'rendered':True,'viewport_contained':False,'text_unclipped':False,'unsupported_css_absent':True,'possible_overlay_absent':False,'fully_visible':False} for e in c['elements']], 'business_headers':[{**h,'geometry':self.geometry()} for h in s['headers']],'business_cells':[{**row,'cells':[{**cell,'geometry':self.geometry()} for cell in row['cells']]} for row in s['rows']],'business_date':{'selector':s['date_selector'],'text':next(e['expected_text'] for e in c['elements'] if e['kind']=='date-filter'),'geometry':self.geometry()}}
  if self.ellipsis:
   cell=out['business_cells'][0]['cells'][2];clip={'selector':cell['text_selectors'][0],'supported':True,'text_overflow':'ellipsis','line_clamp':'none','overflow_x':'hidden','overflow_y':'hidden','client_width':100,'client_height':20,'scroll_width':150,'scroll_height':20};cell['geometry'].update(text_unclipped=False,text_clips=[clip],preview_required=True)
  return out
 def request(self,c):
  i=self.inputs()
  if c['op']=='tabs':return {'ok':True,'result':[{'windowId':i['command']['windowId'],'focused':True,'tabs':[{'tabId':i['command']['tabId'],'windowId':i['command']['windowId'],'active':True,'allowed':True,'url':i['url'],'title':'来客'}]}]}
  base=self.base(i)
  if c['op']=='viewport-proof':return {'ok':True,'result':base}
  self.assertEqual(c['op'],'dom-region-proof');selected=c['selectors'];groups=[row for row in base['business_cells'] if all(cell['selector'] in selected for cell in row['cells'])];coverage={'contract':b.CONTRACT,'notice_ids':[row['notice_id'] for row in groups],'date_filter_visible':base['business_date']['selector'] in selected,'list_headers_visible':all(h['selector'] in selected for h in base['business_headers']),'cell_text_completeness':{row['notice_id']:[{'field':cell['field'],'text_complete_in_image':cell['geometry']['text_unclipped']} for cell in row['cells']] for row in groups}}
  return {'ok':True,'result':{'source':'local-dom-bridge','method':'public-DOM-evidence-region-proof','geometry_purpose':'evidence-crop-only','pixel_input_actions':False,'external_painted_overlap':False,'scope':base['scope'],'url':i['url'],'base_proof':base,'selectors':selected,'region':{'left':300,'top':200,'right':1100,'bottom':400,'width':800,'height':200},'viewport':{'width':1440,'height':763,'device_pixel_ratio':2,'visual_scale':1},'safety_version':base['safety_version'],'evidence_contract':b.CONTRACT,'region_build':'region-notice-business-cells-v1','occlusion_verified':False,'paint_audit':{'contract':'public-DOM-business-paint-audit-v1','unpainted_count':0,'preserved_count':0,'unresolved_count':0},'derived_business_coverage':coverage,'quality_review_required':any(not x['text_complete_in_image'] for fields in coverage['cell_text_completeness'].values() for x in fields)}}
 def frame(self,page,mode,key):
  self.page=page;value=r.capture(self.src,self.q['pages'][page-1]['observation'],self.pr,pid=55,mode=mode,chain_id='business-five-chain',key=key,outdir=self.root/key,revision='r1',request=self.request,native=self.native,ax=self.ax)
  if value['state']=='awaiting-visual-review':
   m=r.sr.document(r.ref(value['metadata']));facts=r.frame_facts(m['public_dom_proof']['before'],r.metadata_inputs(m));att=self.write(key+'-attestation.json',{'kind':'violation-frame-region-quality-attestation-v1','reviewer_role':'supervisor','decision':'approved','registration_preview':r.ref(value['metadata']),'binding':r.quality_binding(m),'field_visibility':b.expected_visibility(mode,facts),'reviewed_at':r.stamp()});value=r.approve_preview(value['metadata'],att)
  self.paths.append(value['metadata']);return value
 def test_new_explicit_profile_preserves_old_default_and_derives_actual_five_fields(self):
  old=profile_api.derive(self.src,self.job,self.query,full_source_check=False);self.assertNotIn('evidence_contract',old);profile_api.validate(self.profile,self.src);i=self.inputs();self.assertEqual(i['evidence_contract'],b.CONTRACT);self.assertTrue(all(e['key'].startswith(b.CONTRACT+':') for e in i['command']['elements']));self.assertEqual(len(i['business_spec']['rows']),10);self.assertEqual(len(i['business_spec']['headers']),5)
  bad=copy.deepcopy(self.profile);bad['evidence_contract']='unknown'
  with self.assertRaises(ValueError):profile_api.validate(bad,self.src)
 def test_old_TR_false_own_boxes_true_and_platform_ellipsis_preview(self):
  i=self.inputs();p=self.base(i);b.validate_base(p,i);self.assertFalse(p['elements'][0]['fully_visible']);request=b.prepare_region_request(i,p,'rows');region=self.request(request)['result'];facts=b.facts(region,i);self.assertEqual(len(facts['notice_ids']),10);self.assertFalse(facts['cell_text_completeness'][facts['notice_ids'][0]][2]['text_complete_in_image']);self.assertTrue(region['quality_review_required']);self.assertNotIn('visible_excerpt_text',json.dumps(region))
  newer=copy.deepcopy(region);newer['region_build']='region-notice-business-cells-v2';self.assertEqual(b.facts(newer,i),facts)
  unknown=copy.deepcopy(region);unknown['region_build']='region-notice-business-cells-v6'
  with self.assertRaises(ValueError):b.facts(unknown,i)
  bad=copy.deepcopy(region);bad['selectors'].pop()
  with self.assertRaises(ValueError):b.facts(bad,i)
 def test_actual018_identity_badge_is_bound_to_same_source_cell_and_retains_raw_transform(self):
  i=self.inputs();p=self.base(i);p['diagnostic_build']='viewport-notice-business-cells-v5';row=next(r for r in p['business_cells'] if r['notice_id']=='202610204776378817');cell=row['cells'][0];actual=json.loads((BASE/'screenshot-observations/018-row5-business-css-v4-readonly-raw.json').read_text());old=next(r for r in actual['reply']['result']['business_cells'] if r['notice_id']==row['notice_id'])['cells'][0]['geometry'];g=copy.deepcopy(old);badge=i['business_spec']['identity_badges'][cell['selector']][0]
  item={**badge,'classification':'reviewed-static-identity-2d-badge-v1','computed_transform':old['unsupported_css_diagnostic']['candidates'][0]['style']['transform'],'identity_components':[1,0,0,1,0,0],'active_or_pending_animation_count':0,'text_present':False,'interactive':False,'geometry_changed':False,'original_css_retained':True};g.update(supported_static_identity_transforms=[item],recursive_unsupported_css_absent=False,unsupported_css_absent=True,evidence_eligible=True);cell['geometry']=g;b.validate_base(p,i);self.assertEqual(g['unsupported_css_diagnostic']['candidates'][0]['style']['transform'],'matrix(1, 0, 0, 1, 0, 0)');self.assertFalse(g['recursive_unsupported_css_absent'])
  for mode in ('matrix','cell','animation','bool','other-css','missing'):
   bad=copy.deepcopy(p);target=next(r for r in bad['business_cells'] if r['notice_id']==row['notice_id'])['cells'][0]['geometry'];decl=target['supported_static_identity_transforms'][0];diag=target['unsupported_css_diagnostic']['candidates'][0]
   if mode=='matrix':decl['computed_transform']=diag['style']['transform']='matrix(1, 0, 0, 1, 0.001, 0)'
   elif mode=='cell':decl['selector']=i['business_spec']['rows'][0]['cells'][0]['selector']
   elif mode=='animation':diag['animation_count']=1
   elif mode=='bool':decl['identity_components'][0]=True
   elif mode=='other-css':diag['reasons'].append('filter');diag['style']['filter']='blur(1px)'
   else:target['supported_static_identity_transforms']=[]
   with self.subTest(mode=mode),self.assertRaises(ValueError):b.validate_base(bad,i)
 def test_table_shadow_metadata_requires_exact_public_template_and_preview(self):
  i=self.inputs();region=self.request(b.prepare_region_request(i,self.base(i),'rows'))['result'];alpha=1-(1-.08)*(1-.04)*(1-.08)
  shadow={'classification':'noninteractive-translucent-table-edge-shadow','structure':'governance-table-column-shadow-end-v1','class':'governance_merchant-Table-ColumnShadow governance_merchant-Table-ColumnShadow_end','parent_class':'governance_merchant-Table-Shadow governance_merchant-Table-Shadow_sticky','container_class':'governance_merchant-Table-Container governance_merchant-Table-Container_scrollable','frame_class':'governance_merchant-Table-Frame','box_shadow':'rgba(16, 17, 20, 0.08) -12px 0px 12px -12px, rgba(16, 17, 20, 0.04) -4px 0px 4px -4px, rgba(16, 17, 20, 0.08) -1px 0px 1px -1px','layer_alphas':[.08,.04,.08],'composited_alpha_upper_bound':alpha,'effective_alpha_upper_bound':alpha,'ancestor_opacity':1,'approved_alpha_limit':.2,'original_pixels_preserved':True,'visual_review_required':True,'foreign_css_effects_absent_except_known_shadow':True}
  region.update(region_build='region-notice-business-cells-v3',preserved_table_shadows=[shadow],quality_review_required=True);region['paint_audit']['preserved_count']=1;b.facts(region,i)
  for field,value in [('box_shadow','opaque'),('class','other'),('effective_alpha_upper_bound',.8),('visual_review_required',False)]:
   bad=copy.deepcopy(region);bad['preserved_table_shadows'][0][field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):b.facts(bad,i)
  region['quality_review_required']=False
  with self.assertRaises(ValueError):b.facts(region,i)
 def test_bad_structure_text_selector_numeric_ellipsis_and_scope_rejected(self):
  i=self.inputs();original=self.base(i)
  for mode in ('order','source','subtree','nan','bool','negative','unknownclip','box','scope'):
   p=copy.deepcopy(original);cell=p['business_cells'][0]['cells'][2];clip=cell['geometry']['text_clips'][0]
   if mode=='order':cell['index']=4
   elif mode=='source':cell['text']='different source'
   elif mode=='subtree':clip['selector']=p['business_cells'][0]['cells'][1]['selector']
   elif mode=='nan':clip['client_width']=float('nan')
   elif mode=='bool':clip['client_width']=True
   elif mode=='negative':clip['scroll_height']=-1
   elif mode=='unknownclip':clip['text_overflow']='clip'
   elif mode=='box':cell['geometry']['box_viewport_contained']=False
   else:p['scope']['groupid']='999'
   with self.subTest(mode=mode),self.assertRaises(ValueError):b.validate_base(p,i)
 def test_complete_16_coverage_from_approved_original_pixel_regions_not_TR_flags(self):
  for page,mode in ((1,'anchor'),(1,'rows'),(2,'anchor'),(2,'rows')):self.frame(page,mode,'business-frame-'+str(len(self.paths)))
  out=self.root/'manifest.json';r.assemble(self.src,self.paths,out);manifest=r.sr.document(r.ref(out));src=r.sr.document(self.src);checked=r.validate_chain(manifest,source=self.src,company=src['company'],groupid=src['groupid'],start=src['start'],end_exclusive=src['end_exclusive'],notice_ids=[row['notice_id'] for row in src['records']['rows']]);self.assertEqual(len(checked['notice_ids']),16);self.assertEqual(checked['visibility_policy'],b.CONTRACT);self.assertEqual(self.captured,4)
 def test_pending_ellipsis_cannot_send_or_forge_completeness_and_no_second_capture(self):
  value=r.capture(self.src,self.q['pages'][0]['observation'],self.pr,pid=55,mode='rows',chain_id='business-five-chain',key='pending-five-rows',outdir=self.root/'pending',revision='r1',request=self.request,native=self.native,ax=self.ax);self.assertEqual(value['state'],'awaiting-visual-review');m=r.sr.document(r.ref(value['metadata']))
  with self.assertRaisesRegex(ValueError,'quality-approval-required'):r.validate_frame(value['image'],m,source=self.src)
  facts=r.frame_facts(m['public_dom_proof']['before'],r.metadata_inputs(m));visibility=b.expected_visibility('rows',facts);notice=facts['notice_ids'][0];visibility['rows'][notice]['object']['text_complete_in_image']=True
  bad=self.write('bad-attestation.json',{'kind':'violation-frame-region-quality-attestation-v1','reviewer_role':'supervisor','decision':'approved','registration_preview':r.ref(value['metadata']),'binding':r.quality_binding(m),'field_visibility':visibility,'reviewed_at':r.stamp()})
  with self.assertRaisesRegex(ValueError,'quality-fields-not-confirmed'):r.approve_preview(value['metadata'],bad)
  with self.assertRaisesRegex(ValueError,'unknown'):r.capture(self.src,self.q['pages'][0]['observation'],self.pr,pid=55,mode='rows',chain_id='new-policy-chain',key='new-key-cannot-recapture',outdir=self.root/'new-attempt',revision='r2',request=self.request,native=self.native,ax=self.ax)
  self.assertEqual(self.captured,1)
 def test_original_unknown_capture_cannot_switch_to_old_profile_or_new_chain(self):
  def fail(cg,out):self.captured+=1;raise ValueError('synthetic SCK unknown')
  self.native.capture=fail
  with self.assertRaisesRegex(ValueError,'SCK unknown'):self.frame(1,'anchor','original-five-unknown')
  old=self.write('old-profile.json',profile_api.derive(self.src,self.job,self.query,full_source_check=False))
  with self.assertRaisesRegex(ValueError,'unknown'):r.capture(self.src,self.q['pages'][0]['observation'],old,pid=55,mode='anchor',chain_id='different-old-policy',key='cannot-bypass-unknown',outdir=self.root/'different-profile',revision='r1',request=self.request,native=self.native,ax=self.ax)
  self.assertEqual(self.captured,1)
 def test_profile_pair_keeps_original_navigation_binding_and_unknown(self):
  import records_region_navigation as nav
  import prepare_records_capture_order as pair
  old=self.write('original-navigation-profile.json',profile_api.derive(self.src,self.job,self.query,full_source_check=False));raw=profile_api.d.document(self.q['pages'][0]['observation']);commands=[]
  def invoke(c):
   commands.append(c)
   if c['op']=='tabs':result=[{'tabs':[raw['tab']]}]
   elif c['op']=='ping':result={'version':profile_api.d.nav.VERSION,'safety':'DOM-only'}
   elif c['op']=='tree':result=raw['tree']
   else:raise AssertionError('unexpected UI input')
   return {'ok':True,'result':result}
  self.nav_file.unlink();original=nav.Runner(self.src,old,invoke);original.s['operations']=[{'key':'original-unknown','state':'unknown','request':{'action':'page','page':2,'notice_id':None}}];original.save();saved=copy.deepcopy(original.s['operations'])
  order=pair.prepare(self.src,old,self.pr,self.root/'capture-order.json')['profile_pair'];value=pair.validate(order,self.src,old);self.assertEqual(value['navigation_profile_ref'],old);self.assertEqual(value['capture_profile_ref'],self.pr)
  with self.assertRaises(ValueError):nav.Runner(self.src,self.pr,invoke,profile_pair=order)
  runner=nav.Runner(self.src,old,invoke,profile_pair=order)
  with self.assertRaisesRegex(ValueError,'prior-unresolved'):runner.run('page',key='new-business-key',page=2)
  self.assertEqual(json.loads(runner.file.read_text())['operations'],saved);self.assertFalse(any(c['op'] in ('click','scroll') for c in commands))
 def test_canonical_navigation_unknown_or_confirmed_cannot_capture(self):
  for state in ('unknown','confirmed'):
   doc=json.loads(self.nav_file.read_text());doc['operations']=[{'key':'original-navigation','state':state}];r.atomic(self.nav_file,doc)
   with self.subTest(state=state),self.assertRaisesRegex(ValueError,'canonical-navigation-unresolved'):self.frame(1,'anchor','blocked-'+state)
   self.assertEqual(self.captured,0)
  doc['operations']=[];doc['binding']['window_id']=999;r.atomic(self.nav_file,doc)
  with self.assertRaisesRegex(ValueError,'navigation-binding-changed'):self.frame(1,'anchor','blocked-binding')
  self.assertEqual(self.captured,0)
 def test_unknown_source_lock_cannot_switch_profile_chain_or_policy(self):
  folder=self.root/'.frame-capture-state';folder.mkdir();r.atomic(folder/'original.json',{'scope':{'source_sha256':self.src['sha256']},'frames':[{'state':'unknown'}]})
  with self.assertRaisesRegex(ValueError,'unresolved'):self.frame(1,'anchor','business-blocked')
  self.assertEqual(self.captured,0)
 def test_uncovered_only_selects_original_order_excluding_verified_completed_first_four(self):
  original=self.base;visible={0,1,2,3}
  def partial(inputs):
   base=original(inputs)
   for index,row in enumerate(base['business_cells']):
    if index not in visible:
     for cell in row['cells']:cell['geometry'].update(box_viewport_contained=False,evidence_eligible=False,preview_required=False)
   return base
  self.base=partial;first=self.frame(1,'rows','original-first-four');first_m=r.sr.document(r.ref(first['metadata']));self.assertEqual(len(first_m['notice_ids']),4)
  visible.clear();visible.update({3,4,5,6,7,8});out=self.root/'uncovered-five'
  result=r.capture(self.src,self.q['pages'][0]['observation'],self.pr,pid=55,mode='rows',chain_id='business-five-chain',key='only-uncovered-five',outdir=out,revision='r2',uncovered_only=True,request=self.request,native=self.native,ax=self.ax)
  m=r.sr.document(r.ref(result['metadata']));selection=m['pinned_inputs']['uncovered_selection'];ids=[row['notice_id'] for row in self.inputs()['business_spec']['rows']]
  self.assertEqual(m['notice_ids'],ids[4:9]);self.assertEqual(selection['covered_notice_ids'],ids[:4]);self.assertEqual(selection['selected_notice_ids'],ids[4:9]);self.assertEqual(selection['prior_frames'],[r.ref(first['metadata'])]);self.assertEqual(self.captured,2)
  r.validate_frame(result['image'],m,source=self.src,allow_preview=True)
  for mode in ('covered','order','missing','source','prefix'):
   bad=copy.deepcopy(selection)
   if mode=='covered':bad['selected_notice_ids'].insert(0,ids[3])
   elif mode=='order':bad['selected_notice_ids'].reverse()
   elif mode=='missing':bad['selected_notice_ids'].pop()
   elif mode=='source':bad['source']={**self.src,'sha256':'0'*64}
   else:bad['prior_frames']=[]
   with self.subTest(mode=mode),self.assertRaises(ValueError):r.selection_ids(bad,self.inputs(),self.src,'business-five-chain',profile_sha256=self.pr['sha256'],base=m['public_dom_proof']['before']['base_proof'])
  same=r.capture(self.src,self.q['pages'][0]['observation'],self.pr,pid=55,mode='rows',chain_id='business-five-chain',key='only-uncovered-five',outdir=out,revision='r2',uncovered_only=True,request=self.request,native=self.native,ax=self.ax);self.assertTrue(same['reused']);self.assertEqual(self.captured,2)
 def test_uncovered_new_flag_cannot_bypass_unknown_or_revise_original_operation(self):
  folder=self.root/'.native-region-frame-state';folder.mkdir();state={'scope':{'source_sha256':self.src['sha256'],'profile_sha256':self.pr['sha256'],'chain_id':'business-five-chain'},'frames':[{'state':'unknown','operation':{'key':'original','outdir':str(self.root/'old')}}]};r.atomic(folder/(r.fc.fingerprint([self.src['sha256'],'business-five-chain'])+'.json'),state)
  for key,out in [('new-key',self.root/'new'),('original',self.root/'old')]:
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,'unknown|original-operation'):r.capture(self.src,self.q['pages'][0]['observation'],self.pr,pid=55,mode='rows',chain_id='business-five-chain',key=key,outdir=out,revision='r1',uncovered_only=True,request=self.request,native=self.native,ax=self.ax)
  self.assertEqual(self.captured,0)
 def test_seam_python_contract_rejects_nonadjacency_large_overlap_and_fake_counts(self):
  inputs=self.inputs();base=self.base(inputs);command=b.prepare_region_request(inputs,base,'rows',notice_ids=[base['business_cells'][1]['notice_id']]);proof=self.request(command)['result'];rows=base['business_cells'];match={'selected_notice_id':rows[1]['notice_id'],'selected_row':rows[1]['tr_selector'],'direction':'preceding-row-bottom','overlap_css_px':2**-16,'row_overlap_css_px':2**-16};seam={'classification':'verified-adjacent-table-float-seam-v1','foreign_notice_id':rows[0]['notice_id'],'foreign_row':rows[0]['tr_selector'],'foreign_selector':rows[0]['tr_selector'],'tag':'TR','tolerance_css_px':2**-15,'original_pixels_preserved':True,'matches':[match]};proof.update(region_build='region-notice-business-cells-v4',adjacent_table_seams=[seam]);proof['paint_audit']['roundoff_count']=1;b.facts(proof,inputs)
  for mode in ('large','nonadjacent','count','pixels','limit'):
   bad=copy.deepcopy(proof);s=bad['adjacent_table_seams'][0]
   if mode=='large':s['matches'][0]['overlap_css_px']=.001
   elif mode=='nonadjacent':s['foreign_notice_id']=rows[3]['notice_id'];s['foreign_row']=rows[3]['tr_selector'];s['foreign_selector']=rows[3]['tr_selector']
   elif mode=='count':bad['paint_audit']['roundoff_count']=0
   elif mode=='pixels':s['original_pixels_preserved']=False
   else:s['tolerance_css_px']=1
   with self.subTest(mode=mode),self.assertRaises(ValueError):b.facts(bad,inputs)
 def test_actual024_border_evidence_requires_v5_one_physical_pixel_direction_and_preview(self):
  inputs=self.inputs();base=self.base(inputs);rows=base['business_cells'];command=b.prepare_region_request(inputs,base,'rows',notice_ids=[rows[1]['notice_id']]);proof=self.request(command)['result'];raw=json.loads((BASE/'screenshot-observations/024-region-v4-td1-original-tool-error-transcription.json').read_text())['original_error_diagnostic_json'];border={'classification':'observed-adjacent-TD-single-physical-pixel-border-v1','side':'bottom','borders':raw['effects']['borders'],'device_pixel_ratio':1.5,'physical_width':.666667*1.5,'maximum_physical_rounding_error':.5e-6*1.5+1e-12,'css_serialization_decimal_places':6,'original_pixels_preserved':True,'visual_review_required':True};seam={'classification':'verified-adjacent-table-float-seam-v1','foreign_notice_id':rows[0]['notice_id'],'foreign_row':rows[0]['tr_selector'],'foreign_selector':rows[0]['cells'][0]['selector'],'tag':'TD','tolerance_css_px':2**-15,'original_pixels_preserved':True,'matches':[{'selected_notice_id':rows[1]['notice_id'],'selected_row':rows[1]['tr_selector'],'direction':'preceding-row-bottom','overlap_css_px':2**-16,'row_overlap_css_px':2**-16}],'preserved_border':border};proof.update(region_build='region-notice-business-cells-v5',adjacent_table_seams=[seam],quality_review_required=True);proof['paint_audit']['roundoff_count']=1;b.facts(proof,inputs)
  for dpr,width in ((2,'0.5px'),(1.6,'0.625px')):
   scaled=copy.deepcopy(proof);v=scaled['adjacent_table_seams'][0]['preserved_border'];v.update(device_pixel_ratio=dpr,physical_width=float(width[:-2])*dpr,maximum_physical_rounding_error=.5e-6*dpr+1e-12);v['borders']['bottom']['width']=width;b.facts(scaled,inputs)
  for mode in ('old-build','DPR','width','color','physical','side','other-edge','preview','TR'):
   bad=copy.deepcopy(proof);s=bad['adjacent_table_seams'][0];v=s['preserved_border']
   if mode=='old-build':bad['region_build']='region-notice-business-cells-v4'
   elif mode=='DPR':v['device_pixel_ratio']=2
   elif mode=='width':v['borders']['bottom']['width']='0.7px'
   elif mode=='color':v['borders']['bottom']['color']='rgb(0, 0, 0)'
   elif mode=='physical':v['physical_width']=1
   elif mode=='side':v['side']='top'
   elif mode=='other-edge':v['borders']['top'].update(style='solid',width='.666667px')
   elif mode=='preview':bad['quality_review_required']=False
   else:s['tag']='TR';s['foreign_selector']=s['foreign_row']
   with self.subTest(mode=mode),self.assertRaises(ValueError):b.facts(bad,inputs)
if __name__=='__main__':unittest.main()

