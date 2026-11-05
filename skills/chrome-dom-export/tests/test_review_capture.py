import base64,copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import review_capture as rc
import review_registration as rr
import bridge
PNG='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGD4DwABBAEAX+XDSwAAAABJRU5ErkJggg=='
class ReviewCaptureTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  source=self.root/'source.json';source.write_text('{"observed_at":"2026-01-01T00:00:00+00:00"}');ref=rc.ref(source)
  self.manifest={k:ref for k in ('job','source','envelope','profile','page')};self.key='123:verified-tuple-sha256:'+'c'*64;self.manifest.update(review_keys=[self.key],capture_key='review-test-001')
  self.command={'op':'review-viewport-proof','tabId':1,'windowId':2,'groupid':'123','source_sha256':ref['sha256'],'dom_sha256':'b'*64,'scope':{'list':'#list','boundary':'#fold','date':'#date','negative':'#neg','count':'#count','other_filters':{'评价类型':'#type','评价来源':'#source','评价状态':'#status'},'date_text':'2026-10-16 ~ 2026-10-19','active_class':'chosen','normal_count':1},'reviews':[{'review_key':self.key,'card':'#card','store':'#store','customer':'#customer','body':'#body','heart':'#heart','store_text':'店','customer_text':'甲','body_text':'正文'}]}
  self.scope={'tabId':1,'windowId':2,'groupid':'123','url':'https://life.douyin.com/p/life_comment/management?groupid=123','title':'来客'}
  g={'rendered':True,'visible_region':True,'viewport_contained':True,'text_unclipped':True,'unsupported_css_absent':True,'occlusion_verified':False,'fully_visible':True};body={**g,'viewport_contained':False,'text_unclipped':True,'fully_visible':False}
  self.proof={'source':'local-dom-bridge','method':'public-DOM-normal-review-viewport-proof','safety_version':rc.visible_capture.SAFETY,'scope':{k:self.command[k] for k in ('tabId','windowId','groupid')},'source_sha256':ref['sha256'],'reference_dom_sha256':'b'*64,'semantic_sha256':'d'*64,'url':self.scope['url'],'viewport_only':True,'pixel_coordinates_returned':False,'pixel_actions_used':False,'occlusion_verified':False,'all_cards_visible':True,'epoch':1,'query':{'date':self.command['scope']['date_text'],'negative_filter':'中差评（1-3心）','normal_count':1,'fold_boundary':'#fold','other_filters':{'评价类型':'全部','评价来源':'全部','评价状态':'全部'}},'reviews':[{'review_key':self.key,'card':'#card','store':'店','customer':'甲','body':'正文','normal_section':True,'card_visible':True,'heart_region_visible':True,'text_complete_in_image':False,'geometry':{'card':g,'store':g,'customer':g,'body':body,'heart':g}}]}
  self.calls=[]
 def request(self,c):
  self.calls.append(c['op'])
  if c['op']=='review-viewport-proof':return {'ok':True,'result':copy.deepcopy(self.proof)}
  return {'ok':True,'result':{'before':self.scope,'after':self.scope,'grant':{'scope':self.scope,'nonce':'nonce','via':'chrome.action.onClicked','safety_version':rc.visible_capture.SAFETY,'invokedAt':'2026-01-01T00:00:00+00:00'},'observedAt':rc.stamp(),'captureKey':c['captureKey'],'safety_version':rc.visible_capture.SAFETY,'capture_method':'chrome.tabs.captureVisibleTab','viewport_only':True,'pixel_actions_used':False,'imageDataUrl':'data:image/png;base64,'+PNG}}
 def run_capture(self):
  with patch.object(rc,'command_from_inputs',return_value=self.command):return rc.capture(self.manifest,self.root/'out',self.request)
 def test_bridge_review_schema_does_not_weaken_notice_schema(self):
  bridge.validate_command(self.command)
  bad=copy.deepcopy(self.command);bad['reviews'][0]['notice_id']='fake'
  with self.assertRaises(ValueError):bridge.validate_command(bad)
 def test_explicit_public_body_v2_schema_preserves_multiline_and_rejects_unknown_contract(self):
  command=copy.deepcopy(self.command);body=command['reviews'][0];body.update(body_text_schema='public-visible-text-v2',body_text='第一行\n第二行');bridge.validate_command(command)
  body['body_text']='长'*16000;bridge.validate_command(command)
  body['body_text']='长'*16001
  with self.assertRaises(ValueError):bridge.validate_command(command)
  body['body_text']='原文';body['body_text_schema']='unreviewed'
  with self.assertRaises(ValueError):bridge.validate_command(command)
 def test_explicit_complete_list_scope_has_real_pagination_and_no_fold_boundary(self):
  c=copy.deepcopy(self.command);c['scope'].pop('boundary');c['scope'].update(scope_mode='verified-complete-normal-list',complete_list={'pager':'#pager','total':'#total','current':'#current','previous':'#previous','next':'#next'});bridge.validate_command(c)
  p=copy.deepcopy(self.proof);p['query'].pop('fold_boundary');p['query'].update(scope_mode='verified-complete-normal-list',normal_list_complete=True,pagination={'total':1,'current':'1/1','previous_disabled':True,'next_disabled':True});self.assertTrue(rc.proof_response({'ok':True,'result':p},c)['all_cards_visible']);self.assertNotIn('fold_boundary',p['query'])
  p['query']['pagination']['next_disabled']=False
  with self.assertRaisesRegex(ValueError,'query-proof-mismatch'):rc.proof_response({'ok':True,'result':p},c)
  c['scope']['complete_list'].pop('next')
  with self.assertRaisesRegex(ValueError,'complete-list'):bridge.validate_command(c)
 def test_capture_collapsed_body_and_offline_registration(self):
  reg=self.run_capture();self.assertFalse(reg['text_complete_in_image'][self.key]);self.assertEqual(self.calls.count('capture-visible'),1)
  with patch.object(rc,'command_from_inputs',return_value=self.command):self.assertTrue(rr.verify(self.root/'out/registration.json')['ok'])
 def test_unknown_never_replays_even_new_output(self):
  def bad(c):
   if c['op']=='capture-visible':self.calls.append(c['op']);raise ValueError('connection-lost')
   return self.request(c)
  with patch.object(rc,'command_from_inputs',return_value=self.command):
   with self.assertRaisesRegex(ValueError,'connection-lost'):rc.capture(self.manifest,self.root/'out',bad)
   with self.assertRaisesRegex(ValueError,'no-replay'):rc.capture(self.manifest,self.root/'out',bad)
   with self.assertRaisesRegex(ValueError,'original-intent'):rc.capture(self.manifest,self.root/'different',bad)
  self.assertEqual(self.calls.count('capture-visible'),1)
 def test_changed_pair_refuses_registration(self):
  original=self.request
  def req(c):
   result=original(c)
   if self.calls.count('review-viewport-proof')>1:result['result']['epoch']=2
   return result
  with patch.object(rc,'command_from_inputs',return_value=self.command):
   with self.assertRaisesRegex(ValueError,'changed-during'):rc.capture(self.manifest,self.root/'out',req)
  self.assertFalse((self.root/'out/registration.json').exists())
 def test_false_derived_visibility_rejected(self):
  self.proof['reviews'][0]['text_complete_in_image']=True
  with self.assertRaisesRegex(ValueError,'visibility-flags'):rc.proof_response({'ok':True,'result':self.proof},self.command)
 def test_wrong_source_and_forged_grant_rejected(self):
  self.proof['source_sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'source-scope'):self.run_capture()
 def test_original_png_tamper_detected(self):
  self.run_capture();(self.root/'out/review.png').write_bytes(b'changed')
  with patch.object(rc,'command_from_inputs',return_value=self.command):
   with self.assertRaisesRegex(ValueError,'png-changed'):rr.verify(self.root/'out/registration.json')
 def test_body_ancestor_clip_visible_region_allowed_but_zero_intersection_refused(self):
  response={'ok':True,'result':self.proof};self.assertTrue(rc.proof_response(response,self.command)['all_cards_visible'])
  self.proof['reviews'][0]['geometry']['body']['visible_region']=False
  with self.assertRaisesRegex(ValueError,'visibility-flags'):rc.proof_response(response,self.command)
 def test_capture_cannot_use_another_tab_same_url(self):
  original=self.request
  def req(c):
   result=original(c)
   if c['op']=='capture-visible':
    result['result']['before']={**self.scope,'tabId':99};result['result']['after']={**self.scope,'tabId':99}
   return result
  with patch.object(rc,'command_from_inputs',return_value=self.command):
   with self.assertRaises(ValueError):rc.capture(self.manifest,self.root/'out',req)
 def test_registration_key_and_time_are_bound(self):
  self.run_capture();path=self.root/'out/registration.json';reg=rc.load(path);reg['capture_key']='different-key-001';path.write_text(json.dumps(reg))
  with patch.object(rc,'command_from_inputs',return_value=self.command):
   with self.assertRaisesRegex(ValueError,'not-complete'):rr.verify(path)
 def test_native_backend_whole_window_registration_and_no_active_tab_needed(self):
  from test_native_window_capture import FakeNative
  native=FakeNative()
  def request(c):
   if c['op']=='tabs':return {'ok':True,'result':[{'windowId':2,'focused':True,'tabs':[{'tabId':1,'windowId':2,'active':True,'allowed':True,'url':self.scope['url'],'title':'来客'}]}]}
   return self.request(c)
  with patch.object(rc,'command_from_inputs',return_value=self.command):
   reg=rc.capture(self.manifest,self.root/'out',request,backend='screen-capture-kit',pid=55,native=native)
   checked=rr.verify(self.root/'out/registration.json')
  self.assertTrue(checked['whole_window']);self.assertFalse(checked['viewport_only']);self.assertEqual(checked['capture_backend'],'screen-capture-kit');self.assertEqual(native.count,1);self.assertNotIn('capture-visible',self.calls);self.assertFalse(reg['text_complete_in_image'][self.key])
 def test_backend_switch_cannot_bypass_issued_unknown_capture(self):
  def failed(c):
   if c['op']=='capture-visible':raise ValueError('unknown Chrome screenshot')
   return self.request(c)
  with patch.object(rc,'command_from_inputs',return_value=self.command):
   with self.assertRaisesRegex(ValueError,'unknown Chrome'):rc.capture(self.manifest,self.root/'out',failed)
   with self.assertRaisesRegex(ValueError,'original-intent'):rc.capture(self.manifest,self.root/'out',self.request,backend='screen-capture-kit',pid=55)
 def repair_fixture(self):
  from test_native_window_capture import FakeNative
  import native_capture_repair as repair
  native=FakeNative()
  def request(c):
   if c['op']=='tabs':return {'ok':True,'result':[{'windowId':2,'focused':True,'tabs':[{'tabId':1,'windowId':2,'active':True,'allowed':True,'url':self.scope['url'],'title':'来客'}]}]}
   return self.request(c)
  good=native.capture
  def fail(*args):native.count+=1;raise ValueError(repair.FAILURE)
  native.capture=fail
  with patch.object(rc,'command_from_inputs',return_value=self.command):
   with self.assertRaisesRegex(ValueError,'CGS_REQUIRE_INIT'):rc.capture(self.manifest,self.root/'out',request,backend='screen-capture-kit',pid=55,native=native)
  state=next((self.root/'.review-capture-state').glob('*.json'));meta=self.root/'out/review.json';original=(state.read_bytes(),meta.read_bytes())
  swift=self.root/'window-capture.swift';swift.write_text('reviewed initialization fix');helper=self.root/'compiled-helper';helper.write_text('compiled');helper.chmod(0o700)
  report={'kind':'sck-initialization-repair-v1','status':'compiled','failure':'CGS_REQUIRE_INIT did_initialize','root_authorization':'retry-readonly-pre-output-once','swift_source':rc.ref(swift),'helper':rc.ref(helper),'source_state':rc.ref(state),'native_metadata':rc.ref(meta)}
  path=self.root/'repair-report.json';path.write_text(json.dumps(report));native.capture=good
  return native,request,rc.ref(path),state,meta,original
 def test_one_same_order_initialization_repair_preserves_both_originals(self):
  native,request,report,state,meta,original=self.repair_fixture()
  with patch.object(rc,'command_from_inputs',return_value=self.command):
   result=rc.capture(self.manifest,self.root/'out',request,backend='screen-capture-kit',pid=55,native=native,repair_report=report)
   self.assertEqual(result['capture_backend'],'screen-capture-kit');self.assertEqual(native.count,2)
   with self.assertRaises(ValueError):rc.capture(self.manifest,self.root/'out',request,backend='screen-capture-kit',pid=55,native=native,repair_report=report)
  intent=rc.load(self.root/'out/native-pre-output-repair.json');self.assertEqual(intent['original_capture_api_issued'],'unknown')
  self.assertEqual(Path(intent['original']['source_state']['path']).read_bytes(),original[0]);self.assertEqual(Path(intent['original']['native_metadata']['path']).read_bytes(),original[1]);self.assertEqual(native.count,2)
 def test_repair_rejects_existing_png_other_error_or_changed_pid(self):
  native,request,report,state,meta,original=self.repair_fixture()
  with patch.object(rc,'command_from_inputs',return_value=self.command):
   with self.assertRaises(ValueError):rc.capture(self.manifest,self.root/'out',request,backend='screen-capture-kit',pid=99,native=native,repair_report=report)
   png=self.root/'out/old.png';png.write_bytes(b'prior screenshot')
   with self.assertRaisesRegex(ValueError,'output-already'):rc.capture(self.manifest,self.root/'out',request,backend='screen-capture-kit',pid=55,native=native,repair_report=report)
   png.unlink();m=rc.load(meta);m['error']='different failure';meta.write_text(json.dumps(m));r=rc.load(report['path']);r['native_metadata']=rc.ref(meta);Path(report['path']).write_text(json.dumps(r));report=rc.ref(report['path'])
   with self.assertRaisesRegex(ValueError,'not-initialization'):rc.capture(self.manifest,self.root/'out',request,backend='screen-capture-kit',pid=55,native=native,repair_report=report)
  self.assertEqual(native.count,1)
 def test_repair_rejects_changed_current_window_and_unknown_retry_never_replays(self):
  import native_capture_repair as repair
  native,request,report,state,meta,original=self.repair_fixture();native.items.reverse()
  with patch.object(rc,'command_from_inputs',return_value=self.command):
   with self.assertRaisesRegex(ValueError,'current-window-changed'):rc.capture(self.manifest,self.root/'out',request,backend='screen-capture-kit',pid=55,native=native,repair_report=report)
   native.items.reverse()
   def fail(*a):native.count+=1;raise ValueError(repair.FAILURE)
   native.capture=fail
   with self.assertRaisesRegex(ValueError,'CGS_REQUIRE_INIT'):rc.capture(self.manifest,self.root/'out',request,backend='screen-capture-kit',pid=55,native=native,repair_report=report)
   with self.assertRaises(ValueError):rc.capture(self.manifest,self.root/'out',request,backend='screen-capture-kit',pid=55,native=native,repair_report=report)
  self.assertEqual(native.count,2)
 def test_real_recorded_normal_join_command(self):
  p=Path(__file__).resolve().parents[3]/'work/live-acceptance/complaints/frozen-20261016-20261020/01-yantai'
  if not (p/'normal-profile.json').exists():self.skipTest('local live evidence unavailable')
  envelope=rc.load(p/'normal-envelope.json');q=self.root/'page.json';q.write_text(json.dumps(envelope['pages'][0],ensure_ascii=False));source=rc.load(p/'authoritative-normal-capture.json');keys=[source['groupid']+':'+r['review_id'] for r in source['rows']]
  command=rc.command_from_inputs(*(rc.ref(p/n) for n in ('navigation-job.json','authoritative-normal-capture.json','normal-envelope.json','normal-profile.json')),rc.ref(q),keys)
  self.assertEqual(len(command['reviews']),4);self.assertEqual(command['scope']['normal_count'],4);bridge.validate_command(command)
 def test_cli_uses_the_formal_bridge_request_transport(self):
  import sys,io,contextlib
  manifest=self.root/'cli-manifest.json';manifest.write_text(json.dumps(self.manifest))
  def capture(manifest,outdir,request,**options):
   self.assertEqual(options,{'backend':'screen-capture-kit','pid':55})
   request({'op':'ping','tabId':1})
   return {'review_keys':[self.key],'text_complete_in_image':{self.key:False}}
  argv=['review_capture.py','--manifest',str(manifest),'--outdir',str(self.root/'cli-out'),'--backend','screen-capture-kit','--pid','55']
  with patch.object(sys,'argv',argv),patch.object(rc,'capture',side_effect=capture),patch.object(bridge,'request',return_value={'ok':True}) as request,contextlib.redirect_stdout(io.StringIO()):
   rc.main()
  request.assert_called_once_with({'op':'ping','tabId':1},timeout=50)
if __name__=='__main__':unittest.main()
