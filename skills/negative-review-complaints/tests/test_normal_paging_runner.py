import sys,json,copy,tempfile,unittest,hashlib
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import normal_paging_runner as r
import test_normal_paging_contract as f
class RunnerTests(unittest.TestCase):
 def setUp(self):
  self.fx=f.ContractTests();self.fx.setUp();self.addCleanup(self.fx.doCleanups);self.root=self.fx.root.resolve();self.base=self.root/'normal-pages-v1';self.base.mkdir();self.page_index=1;self.requests=[]
  self.job=self.fx.job;self.profile=self.fx.profile
  self.jobref=r.publish(self.root/'navigation-job.json',self.job);self.pr=r.publish(self.root/'pending-profile.json',self.profile)
  nav={'fingerprint':hashlib.sha256(json.dumps(self.job,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'tab_id':7,'phase':'observeNegative','revision':3,'calls':[{'state':'confirmed','key':'date-confirmed'}]};self.nr=r.publish(self.root/'navigation-state.json',nav)
  arch=r.immutable(self.base/'original-nav.json',Path(self.nr['path']).read_bytes());jr=r.publish(self.root/'acquisition-journal.json',{})
  self.m={'kind':r.KIND,'job':self.jobref,'original_navigation':self.nr,'navigation_archive':arch,'profile':self.pr,'receipt':self.fx.ref,'source_journal':jr,'root':str(self.root),'tab_id':7,'window_id':8,'code':{},'created_at':r.now()}
  self.mr=r.publish(self.base/'manifest.json',self.m);r.save(self.base/'operation.json',{'kind':r.KIND,'manifest':self.mr,'phase':'read-first','state':'running','expected_page':1,'pages':[],'calls':[],'navigation_sha256':self.nr['sha256']})
  x=patch.object(r,'history_scope',return_value=self.root);x.start();self.addCleanup(x.stop)
 def rpc(self,cmd):
  self.requests.append(copy.deepcopy(cmd));op=cmd['op']
  if op=='tabs':return {'ok':True,'result':[{'tabs':[self.fx.page(self.page_index)['tab']]}]}
  if op=='ping':return {'ok':True,'result':{'version':r.bridge.SAFETY_VERSION,'safety':'DOM-only','content_build':r.CONTENT_BUILD}}
  if op=='tree':return {'ok':True,'result':self.fx.page(self.page_index,terminal=self.page_index==5)['tree']}
  self.assertEqual(op,'click');state=json.loads((self.base/'operation.json').read_bytes());nav=json.loads(Path(self.nr['path']).read_bytes());self.assertEqual(state['state'],'unknown');self.assertEqual(nav['calls'][-1]['state'],'unknown');self.assertEqual(cmd['locator']['value'],'#next');self.page_index+=1
  return {'ok':True,'result':{'kind':'navigation','clicked':{'selector':'#next','name':'','disabled':False,'attributes':{'class':'button-j4VxiA'}}}}
 def test_same_process_stable_two_pages_and_single_durable_click(self):
  out=r.Runner(self.mr,self.rpc).run(5);self.assertEqual((out['state'],out['phase'],out['normal_pages']),('running','ready-next',2));self.assertEqual([x['op'] for x in self.requests].count('click'),1);self.assertFalse(out['all_normal_read']);nav=json.loads(Path(self.nr['path']).read_bytes());self.assertEqual(nav['revision'],3);self.assertEqual(nav['calls'][0],{'state':'confirmed','key':'date-confirmed'});self.assertEqual(nav['calls'][-1]['state'],'confirmed');self.assertTrue((self.base/'navigation-history').is_dir())
 def test_new_process_confirmed_click_only_reads_target_no_replay(self):
  r.Runner(self.mr,self.rpc).run(3);self.requests=[];out=r.Runner(self.mr,self.rpc).run(2);self.assertEqual(out['normal_pages'],2);self.assertNotIn('click',[x['op'] for x in self.requests])
 def test_unknown_click_preserved_restart_zero_requests(self):
  def fail(c):
   if c['op']=='click':raise RuntimeError('lost transport outcome')
   return self.rpc(c)
  out=r.Runner(self.mr,fail).run(3);self.assertEqual(out['state'],'unknown');before=Path(self.nr['path']).read_bytes();self.requests=[];again=r.Runner(self.mr,self.rpc).run(25);self.assertEqual(again['state'],'unknown');self.assertEqual(self.requests,[]);self.assertEqual(before,Path(self.nr['path']).read_bytes());self.assertTrue(list((self.base/'transport').glob('*.json')))
 def test_raw_unknown_terminal_saved_hold_no_next_click(self):
  self.page_index=5;rr=r.Runner(self.mr,self.rpc);rr.s['expected_page']=5;rr.persist();out=rr.run(25);self.assertEqual(out['state'],'hold');self.assertIn('terminal-layout',out['error']);self.assertTrue(r.document(rr.s['latest_page'])['tree']);self.assertNotIn('click',[x['op'] for x in self.requests])
 def test_tab_drift_and_code_drift_do_not_input(self):
  def bad(c):
   out=self.rpc(c)
   if c['op']=='tabs':out['result'][0]['tabs'][0]['windowId']=9
   return out
  self.assertEqual(r.Runner(self.mr,bad).run(25)['state'],'hold');self.assertNotIn('click',[x['op'] for x in self.requests])
 def test_prepare_existing_manifest_cannot_reset_unknown_after_upgrade(self):
  rr=r.Runner(self.mr,self.rpc);rr.run(3);self.requests=[]
  self.assertEqual(r.prepare(self.jobref,self.nr,self.pr),self.mr)
  self.assertEqual(self.requests,[])
 def test_code_bytes_drift_rejected_before_any_bridge_read(self):
  file=self.root/'pinned-code.py';file.write_text('first');m=copy.deepcopy(self.m);m['code']={str(file):r.ref(file)['sha256']};mr=r.publish(self.base/'other-manifest.json',m);s=json.loads((self.base/'operation.json').read_bytes());s['manifest']=mr;r.save(self.base/'operation.json',s);file.write_text('changed');out=r.Runner(mr,self.rpc).run(25);self.assertEqual(out['state'],'hold');self.assertIn('code-changed',out['error']);self.assertEqual(self.requests,[])
 def test_target_not_settled_bounded_reads_never_reclick(self):
  r.Runner(self.mr,self.rpc).run(3);self.page_index=1;self.requests=[];out=r.Runner(self.mr,self.rpc).run(25);self.assertEqual(out['state'],'hold');self.assertIn('did-not-settle',out['error']);self.assertEqual([x['op'] for x in self.requests].count('tree'),3);self.assertNotIn('click',[x['op'] for x in self.requests])
 def test_pending_profile_never_finalizes(self):
  pages,profile=self.fx.finish_pages();pairs=self.fx.pairs(pages,profile);profile['status']='pending-live-multipage-validation'
  with self.assertRaisesRegex(ValueError,'awaits-live-validation'):r.p.finalize_pages(self.job,pages,profile,self.fx.ref,stable_pairs=pairs)
 def review(self,rr):
  raw=r.document(rr.s['latest_page']);profile=copy.deepcopy(self.profile);profile.update(status='live-validated',terminal_layout={'approved_page':rr.s['latest_page'],'page_sha256s':[r.p.A.data_hash(raw)],'boundary_matcher':{'attributes':{'class':'foldTitleContainer-DwIByI'}},'boundary_label':'以下为平台折叠评价'});pr=r.publish(self.root/'approved-profile.json',profile);review={'kind':'normal-paging-terminal-profile-review-v1','manifest':self.mr,'job':self.jobref,'operation_before':r.ref(rr.path),'navigation_sha256':rr.s['navigation_sha256'],'hold_raw':rr.s['latest_page'],'approved_profile':pr,'structure_reviewed':True,'later_pages_live_validated':False};return review
 def test_original_terminal_hold_amend_then_two_fresh_reads_finalize(self):
  rr=r.Runner(self.mr,self.rpc);out=rr.run(25);self.assertEqual(out['state'],'hold');self.assertEqual(out['normal_pages'],4);before=Path(self.nr['path']).read_bytes();review=self.review(rr);rr.approve_profile(r.publish(self.root/'review.json',review));self.assertEqual(before,Path(self.nr['path']).read_bytes());self.requests=[];out=rr.run(25);self.assertEqual(out['state'],'collected');self.assertNotIn('click',[x['op'] for x in self.requests]);final=rr.finalize();self.assertTrue(final['all_normal_read']);self.assertEqual(len(r.document(final['outputs']['source'])['rows']),44);self.assertTrue((self.base/'profile-amendment.json').exists());self.assertTrue(r.document(rr.s['profile_amendment'])['operation_archive'])
 def test_profile_review_wrong_original_state_or_source_refused(self):
  rr=r.Runner(self.mr,self.rpc);rr.run(25);review=self.review(rr);review['operation_before']['sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'review-scope'):rr.approve_profile(r.publish(self.root/'bad-review.json',review))
  self.assertEqual(rr.s['state'],'hold')
if __name__=='__main__':unittest.main()
