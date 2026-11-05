"""Real local crop/validators with synthetic DOM/SCK/AX; no UI or network."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'skills/violation-notifier/scripts'))
import region_frame_capture as r
import native_frame_capture as old

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
fixture=load('region_violation_pages',ROOT/'skills/chrome-dom-export/tests/test_frame_capture.py');transport_fixture=load('region_violation_transport',ROOT/'skills/chrome-dom-export/tests/test_native_window_capture.py');w=load('region_violation_workflow',ROOT/'skills/violation-notifier/scripts/workflow.py')
class RegionFrames(unittest.TestCase):
 def setUp(self):
  self.f=fixture.FrameTests('test_anchor_and_row_frames_keep_visibility_false_and_cover_all_pages');self.f.setUp();self.addCleanup(self.f.doCleanups);self.root=self.f.root;self.native=transport_fixture.FakeNative();self.native.items[0]['kCGWindowBounds']={'X':0,'Y':30,'Width':1440,'Height':850};self.paths=[];self.path=self.root/'region-manifest.json'
  def capture(cg,path):self.native.count+=1;r.region.pillow().new('RGB',(2880,1700),(17,23,42)).save(path);return {'width':2880,'height':1700}
  self.native.capture=capture;self.ax=type('AX',(),{'observe':lambda _,scope:{'pid':55,'url':scope['url'],'AX_main_window':{'x':0,'y':30,'width':1440,'height':850},'AX_webarea':{'x':0,'y':117,'width':1440,'height':763},'webarea_contents_read':False,'geometry_purpose':'evidence-crop-only','input_actions_used':False}})()
 def request(self,c):
  if c['op']=='tabs':return {'ok':True,'result':[{'windowId':3,'focused':True,'tabs':[{'tabId':5,'windowId':3,'active':True,'allowed':True,'url':self.f.source['url']+'&page='+str(self.f.active_page),'title':'来客'}]}]}
  if c['op']=='viewport-proof':return self.f.request(c)
  self.assertEqual(c['op'],'dom-region-proof');base=self.f.request(c['base'])['result'];return {'ok':True,'result':{'source':'local-dom-bridge','method':'public-DOM-evidence-region-proof','geometry_purpose':'evidence-crop-only','pixel_input_actions':False,'external_painted_overlap':False,'scope':base['scope'],'url':base['url'],'base_proof':base,'selectors':c['selectors'],'region':{'left':300,'top':200,'right':1100,'bottom':400,'width':800,'height':200},'viewport':{'width':1440,'height':763,'device_pixel_ratio':2,'visual_scale':1},'safety_version':base['safety_version']}}
 def frame(self,page,mode,**kw):
  self.f.active_page=page;self.f.mode=mode;self.f.sequence+=1;obs=self.f.observation(page);path=self.root/f'region-obs-{self.f.sequence}.json';r.atomic(path,obs);v=r.capture(self.f.source_ref,self.f.ref(path),self.f.profile_ref,pid=55,mode=mode,chain_id=kw.get('chain_id',self.f.chain_id),key='region-test-'+str(self.f.sequence),outdir=self.root/f'region-{self.f.sequence}',revision='r1',request=self.request,native=self.native,ax=self.ax,replaces=kw.get('replaces'));self.paths.append(v['metadata']);return v
 def all_frames(self):
  for page,mode in [(1,'anchor'),(1,'rows'),(2,'anchor'),(2,'rows')]:self.frame(page,mode)
  r.assemble(self.f.source_ref,self.paths,self.path);return json.loads(self.path.read_text())
 def check(self,manifest):return r.validate_chain(manifest,source=self.f.source_ref,company='fixture',groupid='123',start='2026-10-16',end_exclusive='2026-10-20',notice_ids=['notice-1','notice-2','notice-3'])
 def test_exact_original_pixel_regions_cover_all_pages_and_never_select_raw_for_send(self):
  manifest=self.all_frames();checked=self.check(manifest);self.assertTrue(checked['region_only']);self.assertFalse(checked['whole_window']);self.assertEqual(checked['notice_ids'],['notice-1','notice-2','notice-3'])
  for p in self.paths:
   m=json.loads(Path(p).read_text());self.assertEqual(m['image']['width'],1600);self.assertEqual(m['image']['height'],400);self.assertEqual(len(r.validate_frame(m['image']['path'],m,source=self.f.source_ref)['references']),6);self.assertTrue(Path(m['derivation']['source']['path']).is_file())
  batch='fixture';b={'start':'2026-10-16','end_exclusive':'2026-10-20','source':w.evidence(self.root,self.f.source_path),'records':[{'notice_id':'notice-'+str(i)} for i in range(1,4)],'total':3,'send_jobs':{},'screenshots':[]};s={'version':1,'mode':'development','browser_backend':'local-dom-bridge','company':'fixture','groupid':'123','batches':{batch:b},'events':[]};w.add_screenshot_chain(self.root,s,batch,self.path);text=self.root/'copy.txt';text.write_text('fixture');b.update(copy=w.evidence(self.root,text),copy_evidence=w.evidence(self.root,text),artifacts={'source_sha256':b['source']['sha256'],'files':[]})
  with patch.object(w,'validate_artifact_coverage',lambda *_:None):orders=w.send_orders(s,batch)
  images=[o for o in orders if o['part'].startswith('source_list_screenshot:')];self.assertEqual(len(images),4)
  self.assertEqual([o['file_sha256'] for o in images],[json.loads(Path(p).read_text())['image']['sha256'] for p in self.paths]);self.assertTrue(all(o['target']=='测试群请忽略' for o in orders));self.assertNotEqual([o['file_sha256'] for o in images],[json.loads(Path(p).read_text())['derivation']['source']['sha256'] for p in self.paths])
  meta=json.loads(Path(self.paths[0]).read_text());Path(meta['derivation']['source']['path']).write_bytes(b'bad')
  with patch.object(w,'validate_artifact_coverage',lambda *_:None),self.assertRaises(ValueError):w.send_orders(s,batch)
 def test_region_proof_mapping_selectors_and_pixel_tamper_rejected(self):
  v=self.frame(1,'anchor');original=json.loads(Path(v['metadata']).read_text())
  for mode in ('selectors','geometry','whole','pixels'):
   m=copy.deepcopy(original)
   if mode=='selectors':m['pinned_inputs']['region_command']['selectors']=['body']
   elif mode=='geometry':m['geometry_after']['AX']['AX_webarea']['y']+=1
   elif mode=='whole':m['whole_window']=True
   else:m['derivation']['crop_box_pixels'][0]+=1
   with self.subTest(mode=mode),self.assertRaises(ValueError):r.validate_frame(v['image'],m,source=self.f.source_ref)
 def test_unknown_raw_cannot_change_key_chain_revision_or_repeat_capture(self):
  def fail(*a):self.native.count+=1;raise ValueError('synthetic raw unknown')
  self.native.capture=fail
  with self.assertRaisesRegex(ValueError,'raw unknown'):self.frame(1,'anchor')
  for chain in (self.f.chain_id,'new-chain-cannot-bypass'):
   with self.assertRaisesRegex(ValueError,'unknown'):self.frame(1,'anchor',chain_id=chain)
  self.assertEqual(self.native.count,1)
 def test_old_unknown_whole_window_blocks_new_region_before_capture(self):
  folder=self.root/'.native-frame-capture-state';folder.mkdir();r.atomic(folder/'old.json',{'scope':{'source_sha256':self.f.source_ref['sha256']},'frames':[{'state':'unknown'}]})
  with self.assertRaisesRegex(ValueError,'cannot-bypass-unknown'):self.frame(1,'anchor')
  self.assertEqual(self.native.count,0)
 def test_missing_anchor_partial_coverage_and_reversed_pages_hold(self):
  manifest=self.all_frames()
  for frames in (manifest['frames'][1:],manifest['frames'][:-1],list(reversed(manifest['frames']))):
   with self.assertRaises(ValueError):self.check({**manifest,'frames':frames})
 def pending(self,mode='anchor'):
  original=self.request
  def request(c):
   v=original(c)
   if c['op']=='dom-region-proof':v['result'].update(external_painted_overlap='unresolved',quality_review_required=True,occlusion_verified=False,unresolved_overlay=[{'kind':'external-fixed-decoration','painted_alpha':'not-fetched'}])
   return v
  self.request=request;return self.frame(1,mode)
 def attestation(self,v):
  m=json.loads(Path(v['metadata']).read_text());path=self.root/'quality-attestation.json';r.atomic(path,{'kind':'violation-frame-region-quality-attestation-v1','reviewer_role':'supervisor','decision':'approved','registration_preview':r.ref(v['metadata']),'binding':r.quality_binding(m),'field_visibility':{'date_and_headers':m['frame_mode']=='anchor','rows':{i:dict.fromkeys(('reason','subject','object','effective_status','disposal'),True) for i in m['notice_ids']}},'reviewed_at':r.stamp()});return path
 def test_unresolved_preview_is_not_final_and_offline_approval_preserves_original_pixels(self):
  v=self.pending();m=json.loads(Path(v['metadata']).read_text());self.assertEqual(v['state'],'awaiting-visual-review');self.assertEqual(Path(v['metadata']).name,'preview-registration.json')
  with self.assertRaisesRegex(ValueError,'quality-approval-required'):r.validate_frame(v['image'],m,source=self.f.source_ref)
  original=Path(v['metadata']).read_bytes();approved=r.approve_preview(v['metadata'],r.ref(self.attestation(v)));final=json.loads(Path(approved['metadata']).read_text());self.assertEqual(len(r.validate_frame(v['image'],final,source=self.f.source_ref)['references']),8);self.assertEqual(Path(v['metadata']).read_bytes(),original);self.assertEqual(self.native.count,1)
  final['quality_attestation']['sha256']='0'*64
  with self.assertRaises(ValueError):r.validate_frame(v['image'],final,source=self.f.source_ref)
 def test_quality_attestation_cannot_change_page_ids_fields_or_preview(self):
  v=self.pending();path=self.attestation(v);original=json.loads(path.read_text())
  for mode in ('page','id','field','preview','role'):
   a=copy.deepcopy(original)
   if mode=='page':a['binding']['page_scope']['page']=9
   elif mode=='id':a['binding']['notice_ids']=['wrong-id']
   elif mode=='field':a['field_visibility']['date_and_headers']=False
   elif mode=='preview':a['registration_preview']['sha256']='0'*64
   else:a['reviewer_role']='operator'
   r.atomic(path,a)
   with self.subTest(mode=mode),self.assertRaises(ValueError):r.approve_preview(v['metadata'],r.ref(path))
  self.assertEqual(self.native.count,1);self.assertFalse((Path(v['metadata']).parent/'registration.json').exists())
 def test_preview_source_tamper_blocks_approval_without_recapture(self):
  v=self.pending();a=self.attestation(v);Path(self.f.source_ref['path']).write_text('{}')
  with self.assertRaises(ValueError):r.approve_preview(v['metadata'],r.ref(a))
  self.assertEqual(self.native.count,1)
 def test_completed_original_operation_is_readonly_reusable_not_recaptured(self):
  v=self.frame(1,'anchor');m=json.loads(Path(v['metadata']).read_text());b=m['pinned_inputs'];r.capture(self.f.source_ref,{'path':b['observation_path'],'sha256':b['observation_sha256']},self.f.profile_ref,pid=55,mode='anchor',chain_id=self.f.chain_id,key='region-test-1',outdir=self.root/'region-1',revision='r1',request=self.request,native=self.native,ax=self.ax);self.assertEqual(self.native.count,1)
if __name__=='__main__':unittest.main()
