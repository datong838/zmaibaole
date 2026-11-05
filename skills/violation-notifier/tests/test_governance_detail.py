"""Actual public detail fixture + fake connector; never uses a live browser."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_detail as d
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
class DetailTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.query=json.loads((BASE/'records-range-query-v9.json').read_text());self.raw=json.loads((BASE/'first-detail-probe-v9-evidence/0002.json').read_text());self.before=json.loads((BASE/'first-detail-probe-v9-evidence/0001.json').read_text());self.job=json.loads((BASE/'navigation-job.json').read_text());self.row=self.query['rows'][0]
  self.manifest={'kind':'governance-detail-inspection-manifest-v1','inputs':{'job':d.ref(BASE/'navigation-job.json'),'query':d.ref(BASE/'records-range-query-v9.json'),'adopt_probe':d.ref(BASE/'first-detail-probe-v9.json'),'adopt_detail':d.ref(BASE/'first-detail-probe-v9-evidence/0002.json')},'tab_id':995698279,'approved_version':d.nav.VERSION}
 def test_actual_source_query_and_explicit_opened_probe_adoption_no_request(self):
  v=d.inputs(self.manifest);current=d.adopt(self.manifest,v);self.assertEqual(current['notice_id'],self.row['notice_id']);self.assertEqual(current['normal_before'],v['adopt_probe']['calls'][-1]['before'])
 def test_actual_public_recommendation_only_avoid_section_not_internal_rule(self):
  facts,close=d.parse(self.raw,self.row);self.assertTrue(facts['public_recommendation'].startswith('可以前往体验中心'));self.assertNotIn('平台管控阈值',facts['public_recommendation']);self.assertNotIn('判定条例',facts['public_recommendation']);self.assertEqual(facts['object_type'],'门店');self.assertEqual(facts['disposals'],['警告']);self.assertEqual(close['kind'],'dismiss')
 def test_actual_product_title_and_four_advice_paragraphs_remain_section_scoped(self):
  path=BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca/state-evidence/0008.json';raw=json.loads(path.read_text());row=next(x for x in self.query['rows'] if x['notice_id']=='202610204778556479');facts,close=d.parse(raw,row);self.assertEqual(facts['object_type'],'商品');self.assertEqual(len(facts['public_recommendation_paragraphs']),4);self.assertEqual(facts['public_recommendation'].split('\n'),[x['text'] for x in facts['public_recommendation_paragraphs']]);self.assertIn('采购合同/进货单',facts['public_recommendation']);self.assertNotIn('您好，商品素材',facts['public_recommendation']);self.assertNotIn('整改关闭',facts['public_recommendation']);self.assertEqual(close['kind'],'dismiss');self.assertNotIn('public_recommendation_selector',facts)
  wrong=copy.deepcopy(raw);next(n for n in d.g.nodes(wrong['tree']) if n.get('attributes',{}).get('class')=='violationLink-vOK7kM')['attributes']['class']='unreviewed'
  with self.assertRaisesRegex(ValueError,'advice-child-unreviewed'):d.parse(wrong,row)
 def test_wrong_notice_ambiguous_drawer_advice_missing_and_wrong_subject_refuse(self):
  for mode in ('notice','drawer','advice','subject'):
   raw=copy.deepcopy(self.raw);row=copy.deepcopy(self.row)
   if mode=='notice':row['notice_id']='other'
   elif mode=='subject':row['store_name']='other'
   elif mode=='drawer':raw['tree']['root']['children'].append(copy.deepcopy(d.drawers(raw['tree'])[0]))
   else:next(n for n in d.g.nodes(raw['tree']) if n.get('attributes',{}).get('class')=='textView-GrrExP')['attributes']['class']='unreviewed'
   with self.subTest(mode=mode),self.assertRaises(ValueError):d.parse(raw,row)
 def setup_runner(self):
  q=copy.deepcopy(self.query);q['rows']=[self.row];querypath=self.root/'query.json';querypath.write_text(json.dumps(q));m={k:v for k,v in self.manifest.items()};m['inputs']={'job':self.manifest['inputs']['job'],'query':d.ref(querypath)};self.v={'job':self.job,'query':q};self.m=m;self.open=False;self.calls=[];self.lose=None;self.policy=True
 def request(self,c):
  self.calls.append(c)
  if c['op']=='ping':v={'version':d.nav.VERSION,'safety':'DOM-only','governance_query_policy':'observed-dom-20261021-v1',**({'governance_detail_policy':'notice-drawer-close-v1'} if self.policy else {})}
  elif c['op']=='tabs':v=[{'tabs':[self.raw['tab']]}]
  elif c['op']=='tree':v=copy.deepcopy(self.raw['tree'] if self.open else self.before['tree'])
  elif c['op']=='click':
   close=c['kind']=='dismiss';self.open=not close;node=d.g.one([n for n in d.g.nodes(self.raw['tree'] if close else self.before['tree']) if n['selector']==c['locator']['value']],'fake-target')
   if self.lose==('close' if close else 'open'):raise RuntimeError('lost reply')
   v={'kind':c['kind'],'version':d.nav.VERSION,'clicked':node}
  else:raise AssertionError(c)
  return {'ok':True,'result':v}
 def step(self):
  with patch.object(d,'inputs',return_value=self.v):
   r=d.Runner(self.m,self.request);r.step();r.save();return r
 def done(self):
  for _ in range(8):
   r=self.step()
   if r.s['phase']=='complete':return r
  self.fail('incomplete')
 def test_single_open_read_cancel_return_and_repeat_complete_is_offline(self):
  self.setup_runner();r=self.done();self.assertEqual([x['kind'] for x in self.calls if x['op']=='click'],['navigation','dismiss']);self.assertEqual(len(r.s['details']),1);before=len(self.calls);self.step();self.assertEqual(len(self.calls),before)
 def test_open_reply_lost_only_reconciles_same_notice_no_second_open(self):
  self.setup_runner();self.lose='open'
  with self.assertRaisesRegex(RuntimeError,'lost'):self.step()
  self.lose=None;r=self.step();self.assertEqual(r.s['phase'],'close-ready');self.assertEqual(sum(x['op']=='click' for x in self.calls),1);self.assertIn('open_reconciliation',r.s['current'])
 def test_close_reply_lost_only_reconciles_normal_same_notice(self):
  self.setup_runner();self.step();self.step();self.lose='close'
  with self.assertRaisesRegex(RuntimeError,'lost'):self.step()
  self.lose=None;r=self.step();self.assertEqual(r.s['phase'],'complete');self.assertEqual(sum(x['op']=='click' for x in self.calls),2);self.assertIn('close_reconciliation',r.s['details'][0])
 def test_opened_probe_adoption_runner_never_reopens_first_notice(self):
  self.setup_runner();probe=json.loads((BASE/'first-detail-probe-v9.json').read_text());probe['query_ref']=self.m['inputs']['query'];path=self.root/'probe.json';path.write_text(json.dumps(probe));self.m['inputs'].update(adopt_probe=d.ref(path),adopt_detail=d.ref(BASE/'first-detail-probe-v9-evidence/0002.json'));self.v.update(adopt_probe=probe,adopt_detail=self.raw);self.open=True
  self.done();self.assertEqual([x['kind'] for x in self.calls if x['op']=='click'],['dismiss'])
 def test_sixteen_notice_fake_orchestration_includes_unique_page_moves(self):
  self.setup_runner();self.v['query']=self.query;self.page=2;self.open=False
  pages={p['page']:d.document(p['observation']) for p in self.query['pages']}
  def request(c):
   self.calls.append(c)
   if c['op']=='ping':value={'version':d.nav.VERSION,'safety':'DOM-only','governance_detail_policy':'notice-drawer-close-v1'}
   elif c['op']=='tabs':value=[{'tabs':[self.raw['tab']]}]
   elif c['op']=='tree':value=copy.deepcopy(self.raw['tree'] if self.open else pages[self.page]['tree'])
   elif c['op']=='click':
    if c['kind']=='dismiss':self.open=False
    else:
     node=next(n for n in d.g.nodes(pages[self.page]['tree']) if n['selector']==c['locator']['value'])
     if node['tag']=='li':self.page=int(d.g.text(node))
     else:self.open=True
    value={'kind':c['kind'],'version':d.nav.VERSION,'clicked':{}}
   else:raise AssertionError(c)
   return {'ok':True,'result':value}
  def parse(raw,row):return ({'notice_id':row['notice_id'],'public_recommendation':'mock advice only','observed_at':raw.get('observed_at')},{'op':'click','tabId':self.m['tab_id'],'kind':'dismiss','locator':{'by':'selector','value':'#mock-close'}})
  with patch.object(d,'inputs',return_value=self.v),patch.object(d,'parse',side_effect=parse),patch.object(d,'reply_matches'):
   for _ in range(100):
    r=d.Runner(self.m,request);r.step();r.save()
    if r.s['phase']=='complete':break
   self.assertEqual(r.s['phase'],'complete');self.assertEqual(len(r.s['details']),16);self.assertEqual([x['notice_id'] for x in r.s['details']],[x['notice_id'] for x in self.query['rows']]);d.verify_completed(r.s,self.m,self.v)
  clicks=[x for x in self.calls if x['op']=='click'];self.assertEqual(sum(x['kind']=='dismiss' for x in clicks),16);self.assertEqual(len(clicks),34)
 def test_completed_facts_tamper_or_missing_normal_evidence_refuses(self):
  self.setup_runner();r=self.done();s=copy.deepcopy(r.s);s['details'][0]['facts']['public_recommendation']='伪造建议'
  with self.assertRaisesRegex(ValueError,'facts-changed'):d.verify_completed(s,self.m,self.v)
  for index in (0,1):
   s=copy.deepcopy(r.s);s['calls'][index]['result']['clicked']['name']='unreviewed'
   with self.assertRaisesRegex(ValueError,'reply-unverified'):d.verify_completed(s,self.m,self.v)
  s=copy.deepcopy(r.s);s['details'][0]['normal_after']['sha256']='0'*64
  with self.assertRaises(ValueError):d.verify_completed(s,self.m,self.v)
 def test_missing_close_capability_never_creates_click(self):
  self.setup_runner();self.step();self.step();self.policy=False
  with self.assertRaisesRegex(ValueError,'policy-not-loaded'):self.step()
  self.assertEqual(sum(x['op']=='click' for x in self.calls),1)
 def test_new_manifest_cannot_bypass_existing_unknown_state(self):
  self.setup_runner();self.lose='open'
  with self.assertRaises(RuntimeError):self.step()
  self.m=copy.deepcopy(self.m);self.m['inputs']['job']={**self.m['inputs']['job'],'sha256':'0'*64}
  with self.assertRaisesRegex(ValueError,'original-manifest-required'):self.step()
if __name__=='__main__':unittest.main()
