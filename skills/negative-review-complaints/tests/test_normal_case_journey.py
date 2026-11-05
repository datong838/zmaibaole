import sys,json,copy,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import normal_case_journey as j
import normal_paging_runner as c
import test_normal_paging_contract as f
class CaseTests(unittest.TestCase):
 def setUp(self):
  self.fx=f.ContractTests();self.fx.setUp();self.addCleanup(self.fx.doCleanups);self.root=self.fx.root;self.env,self.profile,self.source=self.fx.full();self.target=self.source['rows'][10];self.index=1;self.requests=[]
  self.source_ref=c.publish(self.root/'source.json',self.source);self.im={'root':str(self.root),'review_key':'123:'+self.target['review_id'],'inputs':{'source':self.source_ref}};self.ir=c.publish(self.root/'inspection.json',self.im)
  self.v={'job':self.fx.job,'profile':self.profile,'source':self.source,'envelope':self.env,'page':self.env['pages'][0],'_ledger':{'workspace_kind':'negative-review-appeal-history-only-v1'}}
  self.order={'original_action':self.target['action']}
  for pp in [patch.object(j,'inputs',side_effect=lambda rr:(c.document(rr),self.v,self.order,self.target)),patch.object(j,'casecodes',return_value={})]:pp.start();self.addCleanup(pp.stop)
 def rpc(self,cmd):
  self.requests.append(copy.deepcopy(cmd))
  if cmd['op']=='tabs':return {'ok':True,'result':[{'tabs':[self.env['pages'][self.index-1]['tab']]}]}
  if cmd['op']=='ping':return {'ok':True,'result':{'version':c.bridge.SAFETY_VERSION,'safety':'DOM-only','content_build':c.CONTENT_BUILD}}
  if cmd['op']=='tree':return {'ok':True,'result':self.env['pages'][self.index-1]['tree']}
  self.assertEqual(cmd['op'],'click');state=c.document(c.ref(Path(self.mr['path']).parent/'operation.json'));self.assertEqual(state['state'],'unknown');self.assertEqual(state['calls'][-1]['state'],'unknown');selector=cmd['locator']['value'];self.assertIn(selector,('#next','#previous'));self.index+=1 if selector=='#next' else -1
  return {'ok':True,'result':{'kind':'navigation','clicked':{'selector':selector,'attributes':{'class':'button-j4VxiA'},'name':'','disabled':False}}}
 def test_source_case_version_bound_journey_completes_same_process(self):
  self.mr=j.prepare(self.ir);out=j.CaseRunner(self.mr,self.rpc).run(25);self.assertEqual((out['state'],self.index),('complete',2));self.assertEqual([x['op'] for x in self.requests].count('click'),1);op=c.document(out['operation']);self.assertTrue(op['calls'][0]['key'].startswith(self.mr['sha256']+':'));self.assertNotEqual(op['calls'][0]['key'],'normal-page:1->2');self.requests=[];j.CaseRunner(self.mr,self.rpc).run(25);self.assertEqual(self.requests,[])
 def test_previous_from_terminal_stays_within_verified_normal_source(self):
  self.index=5;self.target=self.source['rows'][30];self.mr=j.prepare(self.ir);out=j.CaseRunner(self.mr,self.rpc).run(25);self.assertEqual((out['state'],self.index),('complete',4));self.assertEqual([x['locator']['value'] for x in self.requests if x['op']=='click'],['#previous'])
 def test_unknown_no_replay_or_new_manifest_bypass(self):
  self.mr=j.prepare(self.ir)
  def fail(cmd):
   if cmd['op']=='click':raise RuntimeError('unresolved transport')
   return self.rpc(cmd)
  self.assertEqual(j.CaseRunner(self.mr,fail).run(25)['state'],'unknown');self.requests=[];self.assertEqual(j.CaseRunner(self.mr,self.rpc).run(25)['state'],'unknown');self.assertEqual(self.requests,[]);new=c.publish(self.root/'other-inspection.json',self.im)
  with self.assertRaisesRegex(ValueError,'original-inspection-required'):j.prepare(new)
 def test_open_drawer_operation_never_navigates(self):
  self.mr=j.prepare(self.ir);rp=j.result_path(self.im);c.save(rp,{'state':'open-unknown'});out=j.CaseRunner(self.mr,self.rpc).run(25);self.assertEqual(out['state'],'hold');self.assertEqual(self.requests,[])
 def test_current_provider_mismatch_holds_without_click(self):
  self.env['pages'][0]['tree']['root']['children'][-1]['name']='服务商BAD';self.mr=j.prepare(self.ir);out=j.CaseRunner(self.mr,self.rpc).run(25);self.assertEqual(out['state'],'hold');self.assertNotIn('click',[x['op'] for x in self.requests])
 def test_new_case_gets_separate_journey_for_legitimate_revisit(self):
  self.mr=j.prepare(self.ir);j.CaseRunner(self.mr,self.rpc).run(25);first=self.mr;self.target=self.source['rows'][0];self.im['review_key']='123:'+self.target['review_id'];self.ir=c.publish(self.root/'inspection-case2.json',self.im);self.mr=j.prepare(self.ir);out=j.CaseRunner(self.mr,self.rpc).run(25);self.assertEqual(out['state'],'complete');self.assertNotEqual(first,self.mr);self.assertEqual(self.index,1)
 def test_existing_open_unknown_handoff_reads_original_not_pager(self):
  rp=j.result_path(self.im);c.save(rp,{'state':'open-unknown','manifest':self.im});out=j.ensure_for_result(self.ir['path'],request=lambda cmd:self.fail('no navigation in opened drawer'));self.assertTrue(out['resume_original_result_only']);self.assertFalse(out['navigation_used'])
 def test_batch_same_process_calls_original_history_reader_and_stops_unknown(self):
  import history_workspace as h
  refs={'source':self.source_ref};key=self.im['review_key'];state={'groupid':'123','sources':{self.source_ref['sha256']:{'inputs':refs,'existing_ids':[key]}}};v={'profile':self.profile,'source':{'rows':[self.target]}}
  with patch.object(h,'load',return_value=state),patch.object(h,'_inputs',return_value=v),patch.object(h,'prepare',return_value={'manifest':self.ir}),patch.object(j,'ensure_for_result',return_value={'state':'complete'}),patch.object(h,'run',return_value={'state':'complete'}) as run:
   out=j.batch(self.root,self.source_ref['sha256'],25);self.assertEqual(out['state'],'complete');self.assertEqual(out['completed_cases'],1);self.assertEqual(run.call_count,1)
  folder=self.root/'normal-case-batches'/self.source_ref['sha256'];c.save(folder/'operation.json',{'manifest':c.ref(folder/'manifest.json'),'state':'running','completed':[]})
  with patch.object(h,'load',return_value=state),patch.object(h,'_inputs',return_value=v),patch.object(h,'prepare',return_value={'manifest':self.ir}),patch.object(j,'ensure_for_result',return_value={'state':'unknown','error':'lost click'}),patch.object(h,'run') as run:
   out=j.batch(self.root,self.source_ref['sha256'],25);self.assertEqual(out['state'],'unknown');run.assert_not_called()
if __name__=='__main__':unittest.main()
