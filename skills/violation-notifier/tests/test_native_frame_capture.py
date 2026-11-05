"""Synthetic DOM+mock SCK, real local adapter and workflow; zero UI."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/violation-notifier/scripts'))
import native_frame_capture as n

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
fixture=load('native_violation_pages',ROOT/'skills/chrome-dom-export/tests/test_frame_capture.py')
transport_fixture=load('native_violation_transport',ROOT/'skills/chrome-dom-export/tests/test_native_window_capture.py')
w=load('native_violation_workflow',ROOT/'skills/violation-notifier/scripts/workflow.py')
class NativeFrames(unittest.TestCase):
 def setUp(self):
  self.f=fixture.FrameTests('test_anchor_and_row_frames_keep_visibility_false_and_cover_all_pages');self.f.setUp();self.addCleanup(self.f.doCleanups);self.root=self.f.root;self.native=transport_fixture.FakeNative();self.paths=[];self.manifest_path=self.root/'native-manifest.json'
 def request(self,c):
  if c['op']=='tabs':return {'ok':True,'result':[{'windowId':3,'focused':True,'tabs':[{'tabId':5,'windowId':3,'active':True,'allowed':True,'url':self.f.source['url']+'&page='+str(self.f.active_page),'title':'来客'}]}]}
  self.assertEqual(c['op'],'viewport-proof');return self.f.request(c)
 def frame(self,page,mode):
  f=self.f;f.active_page=page;f.mode=mode;f.sequence+=1;obs=f.observation(page);path=self.root/f'native-obs-{f.sequence}.json';n.atomic(path,obs);out=self.root/f'native-{f.sequence}.png';r=n.capture(f.source_ref,f.ref(path),f.profile_ref,pid=55,mode=mode,chain_id=f.chain_id,key='native-test-'+str(f.sequence),out=out,request=self.request,native=self.native);self.paths.append(r['metadata']);return r
 def all_frames(self):
  for page,mode in [(1,'anchor'),(1,'rows'),(2,'anchor'),(2,'rows')]:self.frame(page,mode)
  n.assemble(self.f.source_ref,self.paths,self.manifest_path);return json.loads(self.manifest_path.read_text())
 def check(self,manifest):return n.validate_chain(manifest,source=self.f.source_ref,company='fixture',groupid='123',start='2026-10-16',end_exclusive='2026-10-20',notice_ids=['notice-1','notice-2','notice-3'])
 def test_whole_window_transport_has_no_active_tab_grant_or_false_viewport_claim(self):
  manifest=self.all_frames();r=self.check(manifest);self.assertEqual(r['notice_ids'],['notice-1','notice-2','notice-3']);self.assertTrue(r['whole_window']);self.assertFalse(r['viewport_only']);self.assertEqual(self.native.count,4)
  for path in self.paths:
   m=json.loads(Path(path).read_text());cap=n.sr.document(m['capture_metadata']);self.assertNotIn('grant',cap);self.assertEqual(m['capture_backend'],'screen-capture-kit');self.assertFalse(m['viewport_only']);self.assertTrue(m['public_dom_proof']['before']['viewport_only'])
   if m['frame_mode']=='rows':self.assertFalse(m['date_filter_visible']);self.assertFalse(m['list_headers_visible'])
 def test_region_request_uses_only_complete_semantically_bound_elements(self):
  self.f.active_page=1;self.f.mode='rows';self.f.sequence=1;obs=self.f.observation(1);path=self.root/'crop-observation.json';n.atomic(path,obs);inputs=n.fc.page_inputs(self.f.source_ref,self.f.ref(path),self.f.profile_ref);proof=n.fc.proof(inputs['command'],inputs['url'],self.request);request=n.prepare_region_request(inputs,proof,'rows');self.assertEqual(request['op'],'dom-region-proof');self.assertEqual(request['selectors'],['#row2']);self.assertEqual(request['base'],inputs['command']);self.assertEqual(request['purpose'],'evidence-crop-only');self.assertNotIn('rect',request)
  changed=copy.deepcopy(proof);changed['elements'][-1]['locator']['value']='#foreign-row'
  with self.assertRaisesRegex(ValueError,'semantic-binding'):n.prepare_region_request(inputs,changed,'rows')
  with self.assertRaisesRegex(ValueError,'required-content-not-visible'):n.prepare_region_request(inputs,proof,'anchor')
 def test_unknown_original_capture_never_replays_with_different_key(self):
  def fail(*_):raise RuntimeError('synthetic unknown')
  self.native.capture=fail
  with self.assertRaises(RuntimeError):self.frame(1,'anchor')
  count=len(self.f.calls)
  with self.assertRaisesRegex(ValueError,'prior-unknown-no-new-key'):self.frame(1,'anchor')
  self.assertEqual(len(self.f.calls),count)
 def test_backend_scope_png_and_proof_tampering_rejected(self):
  r=self.frame(1,'anchor');original=json.loads(Path(r['metadata']).read_text())
  for kind in ('whole','proof','date','backend','pid'):
   m=copy.deepcopy(original)
   if kind=='whole':m['viewport_only']=True
   elif kind=='proof':m['public_dom_proof']['after']['epoch']+=1
   elif kind=='date':m['page_scope']['start']='2026-10-15'
   elif kind=='backend':m['capture_backend']='chrome-tabs'
   else:m['pinned_inputs']['native_command']['pid']=99
   with self.subTest(kind=kind),self.assertRaises(ValueError):n.validate_frame(r['image'],m,source=self.f.source_ref)
  Path(r['image']).write_bytes(b'bad')
  with self.assertRaises(ValueError):n.validate_frame(r['image'],original,source=self.f.source_ref)
 def test_missing_anchor_or_uncovered_row_and_swapped_frames_rejected(self):
  manifest=self.all_frames()
  for frames in (manifest['frames'][1:],manifest['frames'][:-1],list(reversed(manifest['frames']))):
   with self.assertRaises(ValueError):self.check({**manifest,'frames':frames})
 def workflow(self):
  self.all_frames();batch='fixture-batch';b={'start':'2026-10-16','end_exclusive':'2026-10-20','source':w.evidence(self.root,self.f.source_path),'records':[{'notice_id':'notice-'+str(i)} for i in range(1,4)],'total':3,'send_jobs':{},'screenshots':[]};s={'version':1,'mode':'development','browser_backend':'local-dom-bridge','company':'fixture','groupid':'123','batches':{batch:b},'events':[]};w.add_screenshot_chain(self.root,s,batch,self.manifest_path);return s,b,batch
 def test_workflow_keeps_historical_native_chain_but_blocks_final_whole_window_send(self):
  s,b,batch=self.workflow();entry=b['screenshot_chains'][0];self.assertEqual(entry['capture_backend'],'screen-capture-kit');self.assertTrue(entry['whole_window']);self.assertFalse(entry['viewport_only']);self.assertEqual(len(entry['frames']),4)
  text=self.root/'copy.txt';text.write_text('fixture');b.update(copy=w.evidence(self.root,text),copy_evidence=w.evidence(self.root,text),artifacts={'source_sha256':b['source']['sha256'],'files':[]})
  with patch.object(w,'validate_artifact_coverage',lambda *_:None),self.assertRaisesRegex(ValueError,'whole-window-historical-evidence-not-final-send'):w.send_orders(s,batch)
  entry['capture_backend']=None
  with patch.object(w,'validate_artifact_coverage',lambda *_:None),self.assertRaisesRegex(ValueError,'backend-conflict'):w.send_orders(s,batch)
  entry['capture_backend']='screen-capture-kit';entry['frames'][0],entry['frames'][1]=entry['frames'][1],entry['frames'][0]
  with patch.object(w,'validate_artifact_coverage',lambda *_:None),self.assertRaisesRegex(ValueError,'registered-frame-changed'):w.send_orders(s,batch)
  entry['frames'][0],entry['frames'][1]=entry['frames'][1],entry['frames'][0]
  # Immutable registered refs alone cannot conceal changed original native proof.
  metadata=json.loads(Path(self.paths[0]).read_text());cap=Path(metadata['capture_metadata']['path']);cap.write_text('{}')
  with patch.object(w,'validate_artifact_coverage',lambda *_:None),self.assertRaises(ValueError):w.send_orders(s,batch)
if __name__=='__main__':unittest.main()
