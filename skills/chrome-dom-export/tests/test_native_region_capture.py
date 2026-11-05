import copy,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import native_region_capture as r
class RegionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.geometry={'scope':{'tabId':1,'windowId':2,'groupid':'123','url':'https://life.douyin.com/p/life_comment/management?groupid=123','title':'来客'},'window':{'kCGWindowNumber':77},'CG_bounds':{'x':0,'y':30,'width':1440,'height':850},'AX':{'pid':55,'url':'https://life.douyin.com/p/life_comment/management?groupid=123','AX_main_window':{'x':0,'y':30,'width':1440,'height':850},'AX_webarea':{'x':0,'y':117,'width':1440,'height':763},'webarea_contents_read':False,'geometry_purpose':'evidence-crop-only','input_actions_used':False}}
  self.proof={'method':'public-DOM-evidence-region-proof','geometry_purpose':'evidence-crop-only','pixel_input_actions':False,'external_painted_overlap':False,'scope':{k:self.geometry['scope'][k] for k in ('tabId','windowId','groupid')},'url':self.geometry['scope']['url'],'region':{'left':300,'top':200,'right':1100,'bottom':400,'width':800,'height':200},'viewport':{'width':1440,'height':763,'device_pixel_ratio':2,'visual_scale':1}}
 def test_actual_AX_CG_fixture_derives_toolbar_offset_without_guessing(self):
  p=Path(__file__).resolve().parents[3]/'work/live-acceptance/complaints/live-profile/chrome-native-geometry-fixture.json'
  if not p.exists():self.skipTest('local public geometry fixture unavailable')
  value=json.loads(p.read_text());area=value['webareas'][0];self.assertEqual(area['AXPosition']['value'],{'x':0,'y':117});self.assertEqual(value['main_window']['AXPosition']['value'],{'x':0,'y':30})
  self.assertEqual(r.crop_box(self.proof,self.geometry,2880,1700),[600,574,2200,974])
 def test_moved_window_still_uses_measured_origin(self):
  g=copy.deepcopy(self.geometry);g['CG_bounds']['x']=200;g['CG_bounds']['y']=100;g['AX']['AX_main_window']['x']=200;g['AX']['AX_main_window']['y']=100;g['AX']['AX_webarea']['x']=200;g['AX']['AX_webarea']['y']=187
  self.assertEqual(r.crop_box(self.proof,g,2880,1700),[600,574,2200,974])
 def test_viewport_or_scope_or_overlap_mismatch_rejected(self):
  for field in ('scope','viewport','external_painted_overlap'):
   p=copy.deepcopy(self.proof)
   if field=='scope':p['scope']['tabId']=9
   elif field=='viewport':p['viewport']['height']=900
   else:p[field]=True
   with self.subTest(field=field),self.assertRaises(ValueError):r.crop_box(p,self.geometry,2880,1700)
 def test_pure_crop_roundtrip_exact_source_pixels_and_tamper_rejection(self):
  Image=r.pillow();raw=self.root/'raw.png';im=Image.new('RGB',(2880,1700));im.paste((90,80,70),(0,0,2880,1700));im.paste((1,2,3),(600,574,2200,974));im.save(raw)
  value=r.derive(raw,self.proof,self.geometry,self.root/'region.png');self.assertEqual(value['crop_box_pixels'],[600,574,2200,974]);self.assertEqual(value['image']['width'],1600);self.assertTrue(value['region_only']);self.assertFalse(value['whole_window']);self.assertEqual(r.validate(value,self.proof,self.geometry),value['image'])
  Image.new('RGB',(1600,400),(1,2,4)).save(value['image']['path']);value['image']['sha256']=r.sha(value['image']['path'])
  with self.assertRaisesRegex(ValueError,'not-original-source'):r.validate(value,self.proof,self.geometry)
 def test_region_outside_viewport_never_cropped(self):
  self.proof['region']['right']=1500
  with self.assertRaisesRegex(ValueError,'outside-viewport'):r.crop_box(self.proof,self.geometry,2880,1700)
if __name__=='__main__':unittest.main()
