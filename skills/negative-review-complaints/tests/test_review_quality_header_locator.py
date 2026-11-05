"""Pure synthetic OCR geometry; no image, subprocess, UI or actual business data."""
import sys,copy,unittest,importlib.util,json,types,tempfile
from unittest.mock import patch
from pathlib import Path
R=next(p for p in Path(__file__).resolve().parents if (p/'skills/negative-review-complaints/scripts/program_review_quality.py').is_file() and (p/'run_tests.py').is_file());sys.path[:0]=[str(R/'skills/negative-review-complaints/scripts'),str(R/'skills/chrome-dom-export/scripts')]
import program_review_quality as q
def row(text,left,right,top=.1,bottom=.14,confidence=.9):return {'text':text,'confidence':confidence,'box':[left,1-bottom,right-left,bottom-top]}
def method(cells):return {'kind':'local-vision-cell-ocr-v1','recognition_level':'accurate','recognition_languages':['zh-Hans','en-US'],'language_correction':False,'CPU_only':True,'elapsed_seconds':0,'cells':cells}
class Bounds(unittest.TestCase):
 def setUp(self):
  self.p={'image':{'width':1000,'height':500},'fields':{'score':'较差','store':'餐厅','customer':'张**3','body_visible_fragment':'不好吃','action':'投诉'},'source_score':2,'original_body_complete_flag':False,'has_merchant_reply':True,'source_has_customer_badge':True,'cells':[{'key':'single-original-card','box':[0,0,1000,500]}]}
  self.rows=[row('较差',.02,.08),row('不好',.2,.25),row('吃',.251,.27),row('餐厅',.5,.6),row('①张*3',.72,.82,confidence=.3),row('Lv.5',.83,.87),row('投诉',.9,.96),row('商家回复',.2,.35,.6,.64),row('@张**3',.7,.8,.65,.69)]
  self.first=method([{'key':'single-original-card','box':[0,0,1000,500],'observations':self.rows,'ranges':[{'field':'customer','text':'张**3','box':[.7,.31,.1,.04]}]}])
 def second(self,roi,customer='张**3',confidence=.9):
  return method([{'key':r['key'],'box':r['box'],'observations':[row(customer if r['key']=='customer' else self.p['fields'][r['key']],.1,.9,.3,.7,confidence if r['key']=='customer' else .9)]} for r in roi['cells']])
 def test_header_hint_is_only_locator_and_second_literal_is_required(self):
  roi=q.localize(self.p,self.first);self.assertEqual(roi['nickname_locator']['observation_index'],4);self.assertEqual(roi['nickname_locator']['excluded_badge_indices'],[5]);box=next(c['box'] for c in roi['cells'] if c['key']=='customer');self.assertLess(box[3],.6*500);self.assertEqual(q.evaluate(self.p,self.second(roi),roi)['customer']['expected'],'张**3')
  for text,confidence in [('①张*3',.9),('@张**3',.9),('Lv.5',.9),('张**3',.49)]:
   with self.subTest(text=text,confidence=confidence),self.assertRaises(ValueError):q.evaluate(self.p,self.second(roi,text,confidence),roi)
 def test_reply_only_or_duplicate_header_cannot_locate_customer(self):
  self.rows.pop(4)
  with self.assertRaisesRegex(ValueError,'nickname-range-unavailable'):q.localize(self.p,self.first)
  self.rows.insert(4,row('noise',.72,.77));self.rows.insert(5,row('another',.78,.82))
  with self.assertRaisesRegex(ValueError,'nickname-range-unavailable'):q.localize(self.p,self.first)
 def test_badge_before_name_or_two_badges_refuses(self):
  self.rows[4]=row('wrong',.82,.87);self.rows[5]=row('Lv.5',.72,.78)
  with self.assertRaisesRegex(ValueError,'badge-order'):q.localize(self.p,self.first)
  self.rows[4]=row('Lv.6',.82,.87)
  with self.assertRaisesRegex(ValueError,'badge-not-unique'):q.localize(self.p,self.first)
 def test_horizontal_literal_join_rejects_reverse_overlap_gap_and_ambiguity(self):
  pool=q.observations({'observations':[row('不好',.2,.25),row('吃',.251,.27)]},1000,500,.5);self.assertEqual(len(q.runs('不好吃',pool,1000,500)),2)
  for tail in [row('吃',.17,.19),row('吃',.23,.27),row('吃',.35,.39),row('吃',.251,.27,.3,.34)]:
   pool=q.observations({'observations':[row('不好',.2,.25),tail]},1000,500,.5)
   with self.assertRaises(ValueError):q.runs('不好吃',pool,1000,500)
  pool=q.observations({'observations':[row('不好',.2,.25),row('吃',.251,.27),row('不好吃',.2,.27)]},1000,500,.5)
  with self.assertRaisesRegex(ValueError,'ambiguous'):q.runs('不好吃',pool,1000,500)
 def test_body_tail_from_reply_or_another_column_cannot_complete_literal(self):
  for tail in [row('吃',.251,.27,.65,.69),row('吃',.61,.65)]:
   self.rows[2]=tail
   with self.assertRaises(ValueError):q.localize(self.p,self.first)


ROOT=R
import review_region_capture as rr
class DurableTEMP(unittest.TestCase):
 def setUp(self):
  # Candidate tests reuse the installed, pinned local OCR runtime; fakeOCR
  # intercepts subprocess entirely. Formal post-publication path is identical.
  p=patch.object(q,'__file__',str(R/'skills/negative-review-complaints/scripts/program_review_quality.py'));p.start();self.addCleanup(p.stop)
 def test_program_create_original_approve_register_and_reentry_TEMP_only(self):
  import importlib.util,subprocess
  from unittest.mock import Mock
  spec=importlib.util.spec_from_file_location('review_region_fixture_program',ROOT/'skills/chrome-dom-export/tests/test_review_region_capture.py');fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture);f=fixture.RegionCaptureTests();f.setUp()
  try:
   base=f.f;root=base.root.resolve();sourcerow={'review_id':'verified-tuple-sha256:'+'c'*64,'stars':3,'store':'店','customer':'甲','text':'正文','action':'投诉审核中'}
   node=lambda cls,name='',children=None:{'selector':'#'+cls,'attributes':{'class':cls},'name':name,'tag':'div','children':children or []}
   card={'selector':'#card','attributes':{'class':'commentItem-jrXo5p'},'children':[node('main-OjCeVu',children=[node('firstColumn-aItX1o',children=[node('text-J4lpcH','一般')]),node('secondColumn-NC8I04','正文'),node('poiColumn-dQUMXM','店'),node('customAndButtonColumn-GlYUOL','甲 投诉审核中')])]}
   value={'observed_at':'2026-01-01T00:00:00+00:00','groupid':'123','rows':[sourcerow],'tree':{'root':card}}
   path=root/'source.json';path.write_text(json.dumps(value,ensure_ascii=False));sr=q.ref(path);base.manifest.update({k:sr for k in('job','source','envelope','profile','page')});base.command['source_sha256']=sr['sha256'];base.proof['source_sha256']=sr['sha256'];f.region.update(base_proof=copy.deepcopy(base.proof),external_painted_overlap='unresolved',unresolved_overlay=[{'classification':'synthetic-watermark'}],quality_review_required=True)
   with patch.object(rr.rc,'command_from_inputs',return_value=base.command):
    v=rr.capture(base.manifest,root/'program-capture',f.request,pid=55,revision='program-r1',native=f.native,ax=f.ax);preview=q.ref(root/'program-capture/preview-registration.json')
    def fakeOCR(argv,**kw):
     pp=json.loads(Path(argv[-1]).read_bytes())
     if pp['kind']=='program-review-card-plan-v1':
      specs=[('一般',[.02,.85,.03,.08]),('正文',[.12,.85,.12,.08]),('店',[.62,.85,.03,.08]),('甲',[.78,.85,.03,.08]),('投诉审核中',[.9,.75,.08,.08])];cells=[{'key':'single-original-card','box':pp['cells'][0]['box'],'observations':[{'text':t,'confidence':1,'box':b}for t,b in specs],'ranges':[{'field':'customer','text':'甲','confidence':1,'box':[.78,.85,.03,.08]}]}]
     else:
      fields={'score':'一般','body_visible_fragment':'正文','store':'店','customer':'甲','action':'投诉审核中'};cells=[{'key':c['key'],'box':c['box'],'observations':[{'text':fields[c['key']],'confidence':1,'box':[.1,.1,.8,.8]}],'ranges':[]}for c in pp['cells']]
     return subprocess.CompletedProcess(argv,0,json.dumps({'kind':'local-vision-cell-ocr-v1','recognition_level':'accurate','recognition_languages':['zh-Hans','en-US'],'language_correction':False,'CPU_only':True,'elapsed_seconds':.1,'cells':cells}).encode(),b'')
    runner=Mock(side_effect=fakeOCR)
    with patch.object(q,'subprocess',types.SimpleNamespace(run=runner)):
     a=q.create(preview,root/'program-capture/program-quality');self.assertEqual(runner.call_count,2);done=rr.approve_preview(preview['path'],a);self.assertEqual(done['state'],'complete');self.assertTrue(rr.verify(root/'program-capture/registration.json')['ok']);self.assertEqual(q.create(preview,root/'program-capture/program-quality'),a);self.assertEqual(runner.call_count,2)
    self.assertEqual(f.native.count,1)
  finally:f.doCleanups()

if __name__=='__main__':unittest.main()
