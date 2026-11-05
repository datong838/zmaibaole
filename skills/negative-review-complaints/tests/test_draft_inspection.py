import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import draft_inspection as d
PROJECT=Path(__file__).resolve().parents[3]
BASE=PROJECT/'work/live-acceptance/complaints/frozen-20261020-20261021/01-yantai'
class DraftInspectionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.legacy_patch=patch.object(d,'LEGACY',self.root/'legacy');self.legacy_patch.start();self.addCleanup(self.legacy_patch.stop)
  self.form=json.loads((BASE/'draft-inspection/form-read-1.json').read_text());self.old=json.loads((BASE/'draft-inspection/operation.json').read_text());self.job=json.loads((BASE/'navigation-job.json').read_text());self.before=json.loads((BASE/'draft-inspection/normal-before.json').read_text());self.after=json.loads((BASE/'draft-inspection/normal-after-1.json').read_text())
  self.v={'job':self.job,'profile':{},'page':self.before};self.o={'card_selector':'#card','original_action':'投诉'};self.row={};self.m={'kind':'complaint-draft-inspection-manifest-v1','root':str(self.root),'review_key':self.old['review_key'],'inputs':{'source':{'sha256':self.old['source_sha256']}}};self.action=self.old['open_reply']['clicked'];self.open=False;self.calls=[]
 def mock_inputs(self):return patch.object(d,'inputs',return_value=(self.v,self.o,self.row))
 def request(self,c):
  self.calls.append(c)
  if c['op']=='activate':return {'ok':True,'result':{}}
  if c['op']=='tabs':return {'ok':True,'result':[{'tabs':[self.before['tab']]}]}
  if c['op']=='tree':return {'ok':True,'result':copy.deepcopy((self.form if self.open else self.before)['tree'])}
  if c['op']=='click':
   opening=c['kind']=='complaint-draft';self.open=opening
   return {'ok':True,'result':copy.deepcopy(self.old['open_reply' if opening else 'close_reply'])}
  raise AssertionError(c)
 def tick(self):
  with self.mock_inputs(),patch.object(d,'normal_page',return_value=self.action):return d.tick(self.m,self.request)
 def test_actual_twelve_options_and_utf16_limits_empty(self):
  facts,c=d.options(self.form,self.job);self.assertEqual(facts['options'],d.OPTIONS);self.assertEqual(c,self.old['close_command']);self.assertFalse(facts['platform_selected_in_ui'])
 def test_option_changed_or_selected_reason_nonempty_rejects(self):
  for kind in ('selected','name','reason'):
   p=copy.deepcopy(self.form);nodes=d.normal.flatten(p['tree']['root'])
   if kind=='reason':next(n for n in nodes if n.get('name')=='0 / 300' and n.get('tag')=='textarea')['attributes']['value']='x'
   else:
    label=next(n for n in nodes if n.get('tag')=='label' and n.get('name')=='其他');label['name']='unreviewed' if kind=='name' else '其他'
    if kind=='selected':label['attributes']['class']+=' byted-radio-checked'
   with self.assertRaises(ValueError):d.options(p,self.job)
 def test_single_open_cancel_complete_then_readonly(self):
  for _ in range(7):
   out=self.tick()
   if out['state']=='complete':break
  self.assertEqual(out['state'],'complete');self.assertEqual([x['kind'] for x in self.calls if x['op']=='click'],['complaint-draft','dismiss']);n=len(self.calls);self.tick();self.assertEqual(len(self.calls),n)
 def test_lost_open_reply_reconciles_without_second_open(self):
  self.tick();original=self.request
  def lost(c):
   r=original(c)
   if c['op']=='click':raise RuntimeError('lost')
   return r
  with self.mock_inputs(),patch.object(d,'normal_page',return_value=self.action):
   with self.assertRaises(RuntimeError):d.tick(self.m,lost)
  self.assertEqual(self.tick()['state'],'close-ready');self.assertEqual(len([x for x in self.calls if x['op']=='click']),1)
 def test_lost_cancel_reply_does_not_repeat_cancel(self):
  self.tick();self.tick();self.tick();original=self.request
  def lost(c):
   r=original(c)
   if c['op']=='click':raise RuntimeError('lost')
   return r
  with self.mock_inputs(),patch.object(d,'normal_page',return_value=self.action):
   with self.assertRaises(RuntimeError):d.tick(self.m,lost)
  self.assertEqual(self.tick()['state'],'complete');self.assertEqual(len([x for x in self.calls if x['op']=='click']),2)
 def test_unknown_cannot_bypass_with_new_source(self):
  self.tick();self.m['inputs']['source']['sha256']='a'*64
  with self.assertRaises(ValueError):self.tick()
 def test_legacy_unfinished_operation_requires_original_explicit_reference(self):
  p=d.LEGACY/'case/draft-inspection/operation.json';p.parent.mkdir(parents=True);p.write_text(json.dumps({'review_key':self.m['review_key'],'state':'opened'}))
  with self.assertRaisesRegex(ValueError,'explicit-adoption'):self.tick()
  self.assertEqual(self.calls,[])
 def test_completed_original_adoption_is_offline_and_original_bytes_unchanged(self):
  self.m.update(completed_operation=d.ref(BASE/'draft-inspection/operation.json'),completed_pages={k:d.ref(BASE/('draft-inspection/'+f)) for k,f in [('normal_before','normal-before.json'),('form','form-read-1.json'),('normal_after','normal-after-1.json')]})
  raw=(BASE/'draft-inspection/operation.json').read_bytes();out=self.tick();self.assertEqual(out['state'],'complete');self.assertEqual(self.calls,[]);self.assertEqual(raw,(BASE/'draft-inspection/operation.json').read_bytes())
 def test_actual_source_completed_adoption_entire_chain_without_bridge(self):
  state=json.loads((PROJECT/'runtime/negative-review-complaints/烟台一成教育文化咨询有限公司/state.json').read_text());(self.root/'state.json').write_text(json.dumps(state,ensure_ascii=False))
  m={'kind':'complaint-draft-inspection-manifest-v1','root':str(self.root),'review_key':self.old['review_key'],'inputs':{k:d.ref(BASE/f) for k,f in [('job','navigation-job.json'),('source','authoritative-normal-capture.json'),('profile','normal-profile.json'),('envelope','normal-envelope.json'),('page','draft-inspection/normal-before.json')]},'completed_operation':d.ref(BASE/'draft-inspection/operation.json'),'completed_pages':{k:d.ref(BASE/('draft-inspection/'+f)) for k,f in [('normal_before','normal-before.json'),('form','form-read-1.json'),('normal_after','normal-after-1.json')]}}
  def forbidden(c):raise AssertionError('adoption cannot access browser')
  out=d.tick(m,forbidden);self.assertEqual(out['state'],'complete');self.assertEqual(d.validate(out['operation'])['options'],d.OPTIONS)
 def test_analysis_gate_exact_mapping_source_and_utf16(self):
  f=self.root/'op.json';f.write_text('{}');a={'category':'同行刷屏','draft':'🌟'*15,'platform_category_evidence':{'inspection_operation':d.ref(f),'category_label':'同行刷评','platform_selected_in_ui':False,'reason_filled_in_ui':False,'submitted':False}};s={'tasks':{'key':{'latest_snapshot':{'sha256':'a'*64}}}}
  with patch.object(d,'validate',return_value={'options':d.OPTIONS}):
   d.validate_analysis(self.root,s,'key',a)
   a['platform_category_evidence']['category_label']='热点事件攻击';d.validate_analysis(self.root,s,'key',a)
   a['category']='批量差评';a['platform_category_evidence']['category_label']='批量差评';d.validate_analysis(self.root,s,'key',a)
   a['category']='同行刷屏';a['platform_category_evidence']['category_label']='同行刷评'
   a['draft']='x'*29
   with self.assertRaisesRegex(ValueError,'utf16'):d.validate_analysis(self.root,s,'key',a)
   a['draft']='x'*301
   with self.assertRaisesRegex(ValueError,'utf16'):d.validate_analysis(self.root,s,'key',a)
   a['draft']='x'*30;a['platform_category_evidence']['platform_selected_in_ui']=True
   with self.assertRaisesRegex(ValueError,'no-ui-selection'):d.validate_analysis(self.root,s,'key',a)
   a['platform_category_evidence']['platform_selected_in_ui']=False;a['platform_category_evidence']['category_label']='同行刷屏'
   with self.assertRaisesRegex(ValueError,'category'):d.validate_analysis(self.root,s,'key',a)
if __name__=='__main__':unittest.main()
