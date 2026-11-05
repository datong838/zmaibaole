"""Actual frozen prefix + real JS region algorithm + fake native only.
Canonical journal writes are redirected to a temporary file and its SHA asserted.
No bridge, UI, real screenshots, approvals, or business progress writes.
"""
import unittest,json,copy,sys,subprocess,tempfile,importlib.util
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT/'skills/violation-notifier/scripts'),str(ROOT/'skills/chrome-dom-export/scripts')]
import region_frame_capture as r,business_cells_capture as b
spec=importlib.util.spec_from_file_location('native_fake',ROOT/'skills/chrome-dom-export/tests/test_native_window_capture.py');fake=importlib.util.module_from_spec(spec);spec.loader.exec_module(fake)
BASE=ROOT/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
ACTUAL=BASE/'region-evidence-business-cells-v1/page1-rows3/proof-replies/base-afe3bfd7e3a5eab2f156829f659f3d9f85308c59f82d621101a19b6d67072ae2.json'
class ActualNeighborPending(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.saved=json.loads(ACTUAL.read_text());cls.op=cls.saved['operation'];node='/Users/feibing/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node';cls.region=json.loads(subprocess.check_output([node,str(ROOT/'skills/chrome-dom-export/tests/helpers/source-neighbor-actual.cjs')]));cls.region['safety_version']=r.SAFETY # normal worker envelope addition only
 def inputs(self):return r.fc.page_inputs(self.op['source'],self.op['observation'],self.op['profile'],screenshot_anchor=self.op['screenshot_anchor'])
 def test_actual_real_region_output_full_python_validation_and_neighbor_ack(self):
  i=self.inputs();command=b.prepare_region_request(i,self.saved['reply']['result'],'rows',notice_ids=['ZS202610174754837331']);r.checked({'ok':True,'result':self.region},command,i);facts=b.facts(self.region,i);self.assertEqual(facts['notice_ids'],['ZS202610174754837331']);self.assertEqual(len(facts['unresolved_source_neighbor_overlap']),6);self.assertTrue(b.expected_visibility('rows',facts)['unresolved_source_neighbor_overlap_acknowledged'])
  for mode in ('source','target','order','table','coverage','foreign','rect','sidecar','paintfalse','count'):
   p=copy.deepcopy(self.region);n=p['unresolved_source_neighbor_overlap'][0]
   if mode=='source':n['source_sha256']='0'*64
   elif mode=='target':n['matches'][0]['selected_notice_id']=n['foreign_notice_id']
   elif mode=='order':n['matches'][0]['foreign_source_index']-=1
   elif mode=='table':n['tbody_selector']='#other-tbody'
   elif mode=='coverage':n['coverage_added']=True
   elif mode=='foreign':n['foreign_selector']=i['business_spec']['rows'][0]['cells'][0]['selector']
   elif mode=='rect':n['matches'][0]['selected_visible_cell_rect']['bottom']-=1;n['matches'][0]['selected_visible_cell_rect']['height']-=1
   elif mode=='sidecar':n['contract']='decoration'
   elif mode=='paintfalse':p['external_painted_overlap']=False
   else:p['paint_audit']['source_neighbor_unresolved_count']=0
   with self.subTest(mode=mode),self.assertRaises(ValueError):b.facts(p,i)
 def test_original_verified_prefix_real_region_function_to_pending_with_fake_native(self):
  with tempfile.TemporaryDirectory() as folder:
   out=Path(folder)/'rows3';op=self.op;file=BASE/'.native-region-frame-state'/(r.fc.fingerprint([op['source']['sha256'],op['chain_id']])+'.json');prior=r.ref(file);lock=file.with_suffix('.lock');self.assertTrue(lock.exists());native=fake.FakeNative();native.pid=op['pid']
   for item in native.items:item['kCGWindowOwnerPID']=op['pid']
   native.items[0]['kCGWindowBounds']={'X':0,'Y':30,'Width':1920,'Height':1104};captures=[]
   def capture(cg,path):captures.append(path);r.region.pillow().new('RGB',(1920,1104),(17,23,42)).save(path);return {'width':1920,'height':1104}
   native.capture=capture;ax=type('AX',(),{'observe':lambda _,scope:{'pid':op['pid'],'url':scope['url'],'AX_main_window':{'x':0,'y':30,'width':1920,'height':1104},'AX_webarea':{'x':0,'y':117,'width':1920,'height':1017},'webarea_contents_read':False,'geometry_purpose':'evidence-crop-only','input_actions_used':False}})()
   def request(c):
    if c['op']=='tabs':return {'ok':True,'result':[{'windowId':self.region['scope']['windowId'],'focused':True,'tabs':[{'tabId':self.region['scope']['tabId'],'windowId':self.region['scope']['windowId'],'active':True,'allowed':True,'url':self.region['url'],'title':'来客'}]}]}
    if c['op']=='viewport-proof':return copy.deepcopy(self.saved['reply'])
    self.assertEqual(c['op'],'dom-region-proof');self.assertEqual(c['selectors'],self.region['selectors']);return {'ok':True,'result':copy.deepcopy(self.region)}
   original=r.atomic;writes=[]
   def redirected(path,value):
    path=Path(path).resolve()
    if path==file.resolve():path=Path(folder).resolve()/'fake-only-chain-state.json'
    self.assertTrue(path.is_relative_to(Path(folder).resolve()),str(path));writes.append(path);return original(path,value)
   with patch.object(r,'atomic',side_effect=redirected):
    value=r.capture(op['source'],op['observation'],op['profile'],pid=op['pid'],mode='rows',chain_id=op['chain_id'],key=op['key'],outdir=out,revision=op['revision'],uncovered_only=True,screenshot_anchor=op['screenshot_anchor'],request=request,native=native,ax=ax)
    self.assertEqual(value['state'],'awaiting-visual-review');meta=r.sr.document(r.ref(value['metadata']));self.assertEqual(meta['notice_ids'],['ZS202610174754837331']);r.validate_frame(value['image'],meta,source=op['source'],allow_preview=True);inspected=r.inspect_registration(value['metadata']);self.assertTrue(inspected['required_visual_confirmation']['unresolved_source_neighbor_overlap_acknowledged']);self.assertEqual(inspected['state'],'awaiting-visual-review')
    with self.assertRaisesRegex(ValueError,'quality-approval-required'):r.validate_frame(value['image'],meta,source=op['source'])
   self.assertEqual(len(captures),1);self.assertEqual(prior,r.ref(file));self.assertEqual(len(meta['pinned_inputs']['uncovered_selection']['covered_notice_ids']),9)
if __name__=='__main__':unittest.main()
