"""Saved actual two-page DOM, fake public bridge only; no UI."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import records_region_navigation as n
BASE=Path(__file__).resolve().parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
class NavigationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.source=n.d.ref(BASE/'complete-governance-source.json');cls.job=n.d.ref(BASE/'navigation-job.json');cls.query=n.d.ref(BASE/'records-range-query-v9.json');cls.profile=n.profile_api.derive(cls.source,cls.job,cls.query,full_source_check=False);cls.pages=[n.d.document(x['observation']) for x in n.d.document(cls.query)['pages']]
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.source_ref=self.write('source.json',n.d.document(self.source));self.p=copy.deepcopy(self.profile);self.p['derivation']['source']=self.source_ref;self.profile_ref=self.write('profile.json',self.p);self.idx=0;self.commands=[];self.mutate=None
  # Profile's actual scope derivation is separately source-backed tested; isolate
  # navigation in a temporary root so no pinned live journal can be touched.
  self.patch=patch.object(n.profile_api,'validate',side_effect=lambda p,s:p);self.patch.start();self.addCleanup(self.patch.stop)
 def write(self,name,value):path=self.root/name;n.d.exclusive(path,value);return n.d.ref(path)
 def bridge(self,c):
  self.commands.append(copy.deepcopy(c));raw=copy.deepcopy(self.pages[self.idx])
  if self.mutate:self.mutate(raw)
  if c['op']=='tabs':r=[{'tabs':[raw['tab']]}]
  elif c['op']=='ping':r={'version':n.d.nav.VERSION,'safety':'DOM-only'}
  elif c['op']=='tree':r=raw['tree']
  else:
   target=n.g.one([x for x in n.g.nodes(raw['tree']) if x.get('selector')==c['locator']['value']],'test-target')
   if c['op']=='click':self.idx=1-self.idx;r={'kind':c['kind'],'version':n.d.nav.VERSION,'clicked':target}
   else:r={'version':n.d.nav.VERSION,'scrolled':target}
  return {'ok':True,'result':r}
 def runner(self):return n.Runner(self.source_ref,self.profile_ref,self.bridge)
 def test_actual_pages_scroll_restart_and_no_detail_main_write(self):
  cm=n.d.document(n.d.document(self.source)['capture_manifest']);detail=n.d.document(cm['inputs']['detail_manifest']);main=Path(self.query['path']).parent/'governance-detail-operations'/n.d.nav.tag(n.d.document(self.job))/'state.json';original=main.read_bytes()
  r=self.runner();self.assertEqual(r.run('page',key='page-two-1',page=2)['page'],2)
  row=self.pages[1];notice=n.d.normal_page(row['tree'],n.d.document(self.job),n.d.document(self.query))['rows'][0]['notice_id'];self.assertEqual(self.runner().run('row',key='row-first-2',notice_id=notice)['status'],'complete');self.assertEqual(self.runner().run('anchor',key='date-top-1')['status'],'complete')
  count=len([x for x in self.commands if x['op'] in ('click','scroll')]);self.runner().run('row',key='row-first-2',notice_id=notice);self.assertEqual(count,len([x for x in self.commands if x['op'] in ('click','scroll')]));self.assertEqual(main.read_bytes(),original)
 def test_unknown_no_replay_or_new_key(self):
  r=self.runner();orig=self.bridge
  def fail(c):
   if c['op']=='click':raise RuntimeError('unknown response')
   return orig(c)
  r.invoke=fail
  with self.assertRaises(RuntimeError):r.run('page',key='unknown-page',page=2)
  self.assertEqual(self.runner().run('page',key='unknown-page',page=2)['status'],'unknown-readonly-hold')
  with self.assertRaisesRegex(ValueError,'prior-unresolved'):self.runner().run('page',key='new-key-123',page=2)
  self.assertFalse(any(c['op']=='click' for c in self.commands))
 def test_confirmed_page_effect_can_settle_readonly_after_restart(self):
  orig=self.bridge
  def delayed(c):
   old=self.idx;reply=orig(c)
   if c['op']=='click':self.idx=old
   return reply
  r=self.runner();r.invoke=delayed;self.assertEqual(r.run('page',key='delayed-page2',page=2)['status'],'confirmed-awaiting-readonly-effect');self.idx=1
  self.assertEqual(self.runner().run('page',key='delayed-page2',page=2)['status'],'complete');self.assertEqual(len([c for c in self.commands if c['op']=='click']),1)
 def test_wrong_scroll_reply_stays_unknown_no_second_scroll(self):
  orig=self.bridge
  def wrong(c):
   result=orig(c)
   if c['op']=='scroll':result['result']['scrolled']['selector']='#forged'
   return result
  r=self.runner();r.invoke=wrong
  with self.assertRaisesRegex(ValueError,'scroll-reply-unverified'):r.run('anchor',key='scroll-bad-reply')
  self.assertEqual(self.runner().run('anchor',key='scroll-bad-reply')['status'],'unknown-readonly-hold');self.assertEqual(len([c for c in self.commands if c['op']=='scroll']),1)
 def test_pending_capture_blocks_scroll_and_page_but_observe_allowed(self):
  folder=self.root/'.native-region-frame-state';folder.mkdir();n.d.exclusive(folder/'pending.json',{'scope':{'source_sha256':self.source_ref['sha256']},'frames':[{'state':'unknown'}]})
  self.assertEqual(self.runner().run('observe')['status'],'observed')
  for action,kw in [('page',{'page':2}),('anchor',{})]:
   with self.assertRaisesRegex(ValueError,'capture-frame-unresolved'):self.runner().run(action,key='pending-123',**kw)
  self.assertFalse(any(c['op'] in ('click','scroll') for c in self.commands))
 def test_scope_date_row_corruption_zero_mutations(self):
  for mode in ('group','window','date','row'):
   def change(raw):
    if mode=='group':raw['tab']['url']=raw['tab']['url'].replace('1767942028615694','123456789')
    elif mode=='window':raw['tab']['windowId']+=1
    elif mode=='date':n.g.date_input(raw['tree'])['attributes']['value']='2026/10/15 ～ 2026/10/20'
    else:next(x for x in n.g.nodes(raw['tree']) if 'name-iUMfRa' in n.g.cls(x) and not x.get('children'))['name']='其他主体'
   self.mutate=change
   with self.subTest(mode=mode),self.assertRaises(ValueError):self.runner().run('anchor',key='bad-scope-1')
  self.assertFalse(any(c['op'] in ('click','scroll') for c in self.commands))
 def test_not_in_source_and_key_conflict_and_wrong_ref(self):
  for action,kw in [('page',{'page':3}),('row',{'notice_id':'invented'}),('anchor',{'notice_id':'selector'})]:
   with self.assertRaises(ValueError):self.runner().run(action,key='bad-args-1',**kw)
  self.runner().run('anchor',key='stable-key-1')
  with self.assertRaisesRegex(ValueError,'key-conflict'):self.runner().run('page',key='stable-key-1',page=2)
  with self.assertRaises(ValueError):n.Runner({**self.source_ref,'sha256':'0'*64},self.profile_ref,self.bridge).run('observe')
 def test_reply_persisted_before_guard_and_countdown_name_is_not_business_equality(self):
  original=self.bridge
  def countdown(c):
   reply=original(c)
   if c['op']=='scroll':reply['result']['scrolled']['name']+=' 1天12:12:44'
   return reply
  runner=self.runner();runner.invoke=countdown;notice=n.d.normal_page(self.pages[0]['tree'],runner.job,runner.query)['rows'][4]['notice_id'];result=runner.run('row',key='timer-scroll-reply',notice_id=notice);self.assertEqual(result['status'],'complete');op=json.loads(runner.file.read_text())['operations'][-1];self.assertEqual(op['raw_reply']['result'],op['result'])
  def wrong(c):
   reply=original(c)
   if c['op']=='click':reply['result']['kind']='wrong'
   return reply
  runner=self.runner();runner.invoke=wrong
  with self.assertRaises(ValueError):runner.run('page',key='bad-page-raw',page=2)
  op=json.loads(runner.file.read_text())['operations'][-1];self.assertEqual(op['state'],'unknown');self.assertEqual(op['result']['kind'],'wrong');self.assertEqual(op['raw_reply']['result'],op['result'])
 def test_scroll_countdown_fix_still_rejects_business_tuple_change_after_action(self):
  original=self.bridge
  def changed(c):
   reply=original(c)
   if c['op']=='scroll':
    def mutate(raw):
     page=n.g.records_page(raw['tree'],start=n.d.document(self.job)['start'],end_exclusive=n.d.document(self.job)['end_exclusive']);row=next(x for x in n.g.nodes(raw['tree']) if x.get('selector')==page['rows'][0]['selector']);row['children'][4]['name']='different actual disposal'
    self.mutate=mutate
   return reply
  runner=self.runner();runner.invoke=changed;notice=n.d.normal_page(self.pages[0]['tree'],runner.job,runner.query)['rows'][4]['notice_id']
  with self.assertRaises(ValueError):runner.run('row',key='changed-business-after',notice_id=notice)
  op=json.loads(runner.file.read_text())['operations'][-1];self.assertEqual(op['state'],'confirmed');self.assertIn('raw_reply',op);self.assertIn('result',op);self.assertEqual(len([c for c in self.commands if c['op']=='scroll']),1)
 def reconcile_case(self):
  import prepare_records_capture_order as pairs
  from test_business_cells_capture import BusinessCells
  r=self.runner();notice=n.d.normal_page(self.pages[0]['tree'],r.job,r.query)['rows'][4]['notice_id'];original=self.bridge
  def lost(c):
   if c['op']=='scroll':raise RuntimeError('lost original reply')
   return original(c)
  r.invoke=lost
  with self.assertRaises(RuntimeError):r.run('row',key='lost-row-five',notice_id=notice)
  observed=self.runner().run('observe')['observation'];cap=copy.deepcopy(self.p);cap['evidence_contract']='notice-five-business-cells-v1';capref=self.write('capture-profile.json',cap);pair=pairs.prepare(self.source_ref,self.profile_ref,capref,self.root/'profile-pair.json')['profile_pair'];r=n.Runner(self.source_ref,self.profile_ref,self.bridge,profile_pair=pair)
  inputs=n.profile_api.fc.page_inputs(self.source_ref,observed,capref);fake=object.__new__(BusinessCells);fake.page=1;fake.ellipsis=False;proof=fake.base(inputs);row=next(x for x in proof['business_cells'] if x['notice_id']==notice);row['cells'][0]['geometry'].update(unsupported_css_absent=False,evidence_eligible=False)
  proofref=self.write('viewport-proof.json',{'command':inputs['command'],'reply':{'ok':True,'result':proof},'observation':observed,'input_actions_used':False});return r,observed,proofref,notice
 def test_legacy_lost_scroll_reply_readonly_reconciliation_preserves_original_and_CSS_failure(self):
  r,after,proof,notice=self.reconcile_case();original=r.file.read_bytes();sha=n.d.ref(r.file)['sha256'];self.commands=[];r.invoke=lambda c:self.fail('readonly reconciliation called bridge');result=r.reconcile_scroll('lost-row-five',sha,after,proof);self.assertEqual(result['status'],'readonly-scroll-effect-reconciled');op=result['operation'];self.assertNotIn('result',op);self.assertEqual(op['completion_kind'],'readonly-scroll-effect-reconciled');e=op['reconciliation'];self.assertEqual(Path(e['original_journal']['path']).read_bytes(),original);self.assertFalse(e['API_reply_observed']);self.assertFalse(e['screenshot_permission_verified']);self.assertEqual(e['target_notice_id'],notice);self.assertFalse(e['target_cell_geometry'][0]['geometry']['unsupported_css_absent']);self.assertFalse(e['target_cell_geometry'][0]['geometry']['evidence_eligible']);self.assertFalse(self.commands)
 def test_reconcile_rejects_page_other_unknown_changed_SHA_or_offscreen_target(self):
  r,after,proof,notice=self.reconcile_case();saved=r.file.read_bytes();sha=n.d.ref(r.file)['sha256'];self.commands=[]
  with self.assertRaisesRegex(ValueError,'journal-sha'):r.reconcile_scroll('lost-row-five','0'*64,after,proof)
  for mode in ('page','other','result','box'):
   r.file.write_bytes(saved);state=json.loads(saved)
   if mode=='page':state['operations'][-1]['request']['action']='page'
   elif mode=='other':state['operations'].append({'key':'other-unknown','state':'unknown'})
   elif mode=='result':state['operations'][-1]['result']={'forged':'not-lost'}
   if mode!='box':n.d.exclusive(self.root/(mode+'.json'),state);r.file.write_text(json.dumps(state))
   ref=proof
   if mode=='box':
    p=n.d.document(proof);row=next(x for x in p['reply']['result']['business_cells'] if x['notice_id']==notice);row['cells'][0]['geometry']['box_viewport_contained']=False;ref=self.write('offscreen-proof.json',p)
   with self.subTest(mode=mode),self.assertRaises(ValueError):r.reconcile_scroll('lost-row-five',n.d.ref(r.file)['sha256'],after,ref)
  self.assertFalse(self.commands)
if __name__=='__main__':unittest.main()
