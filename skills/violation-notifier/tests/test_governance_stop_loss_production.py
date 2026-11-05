"""Concrete ports + actual public DOM fixtures, fake connector and temp journals.
Legacy prefix verification is isolated: these tests do not re-prove old9/12 entries.
New parsers/commands/replies/direct source/recovery replay/completion are real.
"""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_detail as d,governance_dom as g
import governance_stop_loss_integration as f,governance_stop_loss_production as p
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
ROLE=BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca'
class ProductionTests(unittest.TestCase):
 def setup_kind(self,kind):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.m=json.loads((BASE/'detail-inspection-manifest.json').read_text());self.v=d.inputs(self.m);q=self.root/'query.json';d.exclusive(q,self.v['query']);self.m['inputs']['query']=d.ref(q)
  name='stop-loss-original-' if kind=='product' else 'rates-stop-loss-original-'
  if kind=='stock':
   notice=self.v['query']['rows'][15]['notice_id'];cached=ROLE/'automatic-stop-loss'/__import__('hashlib').sha256(notice.encode()).hexdigest()/'original-parent.json';source=cached if cached.exists() else ROLE/'state.json';self.parent=json.loads(source.read_text());self.assertEqual(self.parent['current']['notice_id'],notice)
  else:self.parent=json.loads(next(ROLE.glob(name+'*.json')).read_text())
  self.parent['manifest']=self.m;self.parent.pop('hold',None);self.parent.pop('waiting_for',None)
  self.main=p.state_path(self.m,self.v);d.nav.write_json(self.main,self.parent);self.current=d.document(self.parent['last_observation']);self.actions=[];self.requests=[];self.lost=None
  self.restored=d.document(self.v['query']['pages'][0]['observation']);self.page2=d.document(self.v['query']['pages'][1]['observation']);rs=json.loads((ROLE/'rates-recovery/state.json').read_text());self.centers=[d.document(x['observation']) for x in rs['center_pages']]
 def patches(self):
  # Only legacy prefix proof is mocked, never the new source/action/final proof.
  stack=__import__('contextlib').ExitStack();stack.enter_context(patch.object(d,'inputs',return_value=self.v));stack.enter_context(patch.object(d,'verify_completed',return_value=[]));self.addCleanup(stack.close)
 def invoke(self,c):
  self.requests.append(copy.deepcopy(c))
  if c['op']=='tabs':v=[{'tabs':[self.current['tab']]}]
  elif c['op']=='ping':v={'version':d.nav.VERSION,'safety':'DOM-only','governance_query_policy':'observed-dom-20261021-v1','governance_calendar_policy':'date-item-div-v3-single','governance_stop_loss_policy':'public-notice-return-v1','governance_detail_policy':'notice-drawer-close-v1'}
  elif c['op']=='tree':v=copy.deepcopy(self.current['tree'])
  elif c['op']=='click':
   node=g.one([n for n in g.nodes(self.current['tree']) if n.get('selector')==c['locator']['value']],'fake-target-not-unique');self.actions.append(copy.deepcopy(c));v={'version':d.nav.VERSION,'kind':c['kind'],'clicked':copy.deepcopy(node)};name=g.text(node);route=p.urlsplit(self.current['tab']['url']).path
   if name=='查看其他处置':self.current=self.restored
   elif name=='违规中心':self.current=self.centers[0]
   elif route==g.CENTER and name=='2':self.current=self.centers[1]
   elif name=='违规记录':self.current=self.restored
   elif route==g.RECORDS and name=='2':self.current=self.page2
   else:raise AssertionError(('unreviewed command',name,c))
   if self.lost==name:raise RuntimeError('simulated lost reply')
  else:raise AssertionError(c)
  return {'ok':True,'result':v}
 def next(self):
  parent=json.loads(self.main.read_text());ports=p.Ports(self.m,self.invoke);flow=f.Flow(self.m,self.v,parent,ports);return flow.tick(parent)
 def test_product_concrete_ports_restart_after_each_owned_hold_and_finish(self):
  self.setup_kind('product');self.patches()
  for _ in range(4):result=self.next()
  self.assertTrue(result['complete']);parent=json.loads(self.main.read_text());self.assertEqual(parent['cursor'],self.parent['cursor']+1);self.assertEqual(parent['details'][:-1],self.parent['details']);self.assertEqual(len(self.actions),1);self.assertIn('查看其他处置',next(n['name'] for n in g.nodes(d.document(self.parent['last_observation'])['tree']) if n['selector']==self.actions[0]['locator']['value']));self.next();self.assertEqual(len(self.actions),1)
 def cli(self):
  manifest=self.root/'detail-manifest.json';d.nav.write_json(manifest,self.m)
  with patch.object(d.nav.bridge,'request',side_effect=self.invoke),patch.object(sys,'argv',['governance_detail.py','run','--manifest',str(manifest),'--steps','100']),__import__('contextlib').redirect_stdout(__import__('io').StringIO()):return d.main()
 def test_cli_steps100_finishes_stock_without_manual_relaunch(self):
  self.setup_kind('stock');self.patches();self.assertEqual(self.cli(),0);parent=json.loads(self.main.read_text());self.assertEqual(parent['phase'],'complete');self.assertEqual(parent['cursor'],16);self.assertEqual(len(self.actions),4)
 def test_cli_does_not_continue_external_hold_or_parent_unknown(self):
  for mode in ('manual','unknown'):
   self.setup_kind('stock');self.patches();self.next();parent=json.loads(self.main.read_text())
   if mode=='manual':parent['waiting_for']='external-manual-review'
   else:parent['calls'].append({'state':'unknown','command':{'op':'click'},'before':parent['last_observation']})
   d.nav.write_json(self.main,parent);before=len(self.requests);self.assertEqual(self.cli(),0);self.assertEqual(self.actions,[]);self.assertEqual(len(self.requests),before);self.assertEqual(json.loads(self.main.read_text())['cursor'],15)
 def test_script_entrypoint_reuses_canonical_detail_module_identity(self):
  import subprocess
  script=HERE.parents[1]/'scripts/governance_detail.py'
  code="import runpy,sys;sys.path.insert(0,sys.argv[1]);sys.argv=['governance_detail.py','--help'];\ntry:runpy.run_module('governance_detail',run_name='__main__',alter_sys=True)\nexcept SystemExit:pass\nimport governance_detail as d,governance_stop_loss_production as p;assert p.d is d;assert d.__name__=='__main__';print('canonical-detail-module-ok')"
  result=subprocess.run([sys.executable,'-c',code,str(script.parent)],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr);self.assertIn('canonical-detail-module-ok',result.stdout)
 def test_formal_runner_step_detects_after_fresh_observe_and_completes_stock(self):
  self.setup_kind('stock');self.patches();parent=json.loads(self.main.read_text());parent['last_observation']=parent['current']['normal_before'];d.nav.write_json(self.main,parent)
  for _ in range(5):
   r=d.Runner(self.m,self.invoke);r.step()
  parent=json.loads(self.main.read_text());self.assertEqual(parent['cursor'],16);self.assertEqual(parent['details'][-1]['completion_kind'],p.KINDS['stock']);self.assertEqual(len(self.actions),4);self.assertEqual(parent['phase'],'complete');self.assertNotIn('last_error',parent)
 def test_finish_outer_receipt_crash_reconciles_committed_entry_without_ui(self):
  self.setup_kind('product');self.patches()
  for _ in range(4):state=self.next()
  path=f.location(self.m,self.v,self.parent['current']['notice_id']);state['phase']='product_finish';state['complete']=False;state['receipts'].pop();state['calls'][-1].pop('result');state['calls'][-1]['state']='unknown';state['hold']=True;d.nav.write_json(path,state);before=len(self.requests);done=self.next();self.assertTrue(done['complete']);self.assertTrue(done['calls'][-1]['reconciled_from_verified_local_completion']);self.assertEqual(len(self.requests),before)
 def test_formal_dispatch_api_reloads_parent_and_then_yields_to_normal_runner(self):
  self.setup_kind('product');self.patches()
  class Caller:pass
  caller=Caller();caller.manifest=self.m;caller.v=self.v;caller.file=self.main;caller.invoke=self.invoke;caller.s=copy.deepcopy(self.parent)
  for _ in range(4):result=p.dispatch_step(caller)
  self.assertTrue(result['handled']);self.assertTrue(result['complete']);self.assertEqual(caller.s,json.loads(self.main.read_text()));self.assertFalse(p.dispatch_step(caller)['handled']);self.assertEqual(len(self.actions),1)
 def test_rates_direct_sidebar_complete_restarts_each_step_no_arrow_and_pure_replay(self):
  self.setup_kind('rates');self.patches()
  for _ in range(5):result=self.next()
  self.assertTrue(result['complete']);parent=json.loads(self.main.read_text());entry=parent['details'][-1];self.assertEqual(entry['completion_kind'],p.KIND);self.assertEqual(len(self.actions),4);self.assertEqual(self.actions[0]['locator']['value'],p.SIDEBAR);self.assertTrue(all(x['kind']=='navigation' for x in self.actions));p.verify_direct_entry(entry,parent,self.m,self.v,self.v['query']['rows'][12]);self.next();self.assertEqual(len(self.actions),4)
 def test_stock_third_template_direct_sidebar_full_chain_and_own_facts_schema(self):
  self.setup_kind('stock');self.patches()
  for _ in range(5):result=self.next()
  self.assertTrue(result['complete']);parent=json.loads(self.main.read_text());entry=parent['details'][-1];self.assertEqual(entry['completion_kind'],p.KINDS['stock']);self.assertEqual(entry['facts']['schema'],'governance-stock-stop-loss-detail-v1');self.assertEqual(entry['facts']['effective_statuses'],['已撤销']);self.assertNotIn('开通体验补偿赔券',entry['facts']['public_recommendation']);self.assertEqual(len(self.actions),4);self.assertEqual(self.actions[0]['locator']['value'],p.SIDEBAR);p.verify_direct_entry(entry,parent,self.m,self.v,self.v['query']['rows'][15]);mapped=p.capture_mapping(self.v['query']['rows'][15],entry['facts'],entry,state=parent,manifest=self.m,inputs=self.v);self.assertEqual(mapped['detail_object_type_basis']['source_binding']['source_subject'],self.v['query']['rows'][15]['store_name']);self.assertFalse(mapped['detail_object_type_basis']['store_id_observed']);self.assertEqual(mapped['table_effectiveness_status'],'已撤销');self.next();self.assertEqual(len(self.actions),4)
 def test_rates_lost_sidebar_stays_unknown_after_restart_no_second_input(self):
  self.setup_kind('rates');self.patches();self.next();self.lost='违规中心'
  with self.assertRaisesRegex(RuntimeError,'lost reply'):self.next()
  self.lost=None;self.next();self.assertEqual(len(self.actions),1);parent=json.loads(self.main.read_text());self.assertEqual(parent['calls'][-1]['state'],'unknown');self.assertEqual(parent['cursor'],12)
 def test_slow_center_read_is_pending_and_restart_only_reads_then_continues(self):
  self.setup_kind('rates');self.patches();self.next();original=self.current;self.next();self.current=original;pending=self.next();self.assertEqual(pending['phase'],'rates_read_center');self.assertEqual(pending['calls'][-1]['state'],'confirmed');self.assertEqual(len(self.actions),1);self.current=self.centers[0];self.next();self.next();done=self.next();self.assertTrue(done['complete']);self.assertEqual(len(self.actions),4)
 def test_direct_source_immutable_canonical_refs_and_fresh_completed_time_required(self):
  self.setup_kind('rates');self.patches()
  for _ in range(5):self.next()
  parent=json.loads(self.main.read_text());entry=parent['details'][-1];wrong=copy.deepcopy(entry);wrong['recovery_state']=dict(entry['recovery_state']);original=Path(entry['recovery_state']['path']);copied=self.root/original.name;copied.write_bytes(original.read_bytes());wrong['recovery_state']['path']=str(copied)
  with self.assertRaisesRegex(ValueError,'immutable-final'):p.verify_direct_entry(wrong,parent,self.m,self.v,self.v['query']['rows'][12])
 def test_existing_different_final_bytes_are_not_resigned_before_fresh_read(self):
  self.setup_kind('rates');self.patches()
  for _ in range(4):state=self.next()
  previous=state['receipts'][-1];ref=previous['recovery_state'];target=Path(ref['path']).parent/('final-state-'+ref['sha256']+'.json');target.write_bytes(Path(ref['path']).read_bytes()+b'\n');before=len(self.requests)
  with self.assertRaisesRegex(ValueError,'snapshot-conflict'):self.next()
  self.assertEqual(len(self.requests),before)
 def test_pending_child_manual_hold_or_unknown_blocks_before_any_ui_read(self):
  for mode in ('hold','unknown'):
   self.setup_kind('rates');self.patches()
   for _ in range(3):self.next()
   folder=f.location(self.m,self.v,self.parent['current']['notice_id']).parent/'rates-recovery';child={'phase':'select-start','calls':[{'state':'unknown'}] if mode=='unknown' else [],'hold':mode=='hold'};d.nav.write_json(folder/'center-range.json',child);before=len(self.requests)
   with self.subTest(mode=mode),self.assertRaisesRegex(ValueError,'child-unknown|child-external'):self.next()
   self.assertEqual(len(self.requests),before)
 def test_unknown_prior_error_does_not_start_automatic_flow_or_input(self):
  self.setup_kind('stock');self.patches();parent=json.loads(self.main.read_text());parent['last_error']='unknown-transport-or-risk-error';d.nav.write_json(self.main,parent);ports=p.Ports(self.m,self.invoke)
  with self.assertRaisesRegex(ValueError,'not-eligible'):f.Flow(self.m,self.v,parent,ports)
  self.assertEqual(self.requests,[]);self.assertEqual(json.loads(self.main.read_text())['last_error'],'unknown-transport-or-risk-error')
 def test_pure_owned_namedstep_tokens_ignore_readonly_churn_and_retire_after_completion(self):
  self.setup_kind('stock');self.patches();self.next();first=p.verify_owned_progress(self.main);self.assertEqual(first['completed_steps'],['stage']);self.next();second=p.verify_owned_progress(self.main);self.assertEqual(second['progress_tokens'][:1],first['progress_tokens']);p.Ports(self.m,self.invoke).runner().observe();self.assertEqual(p.verify_owned_progress(self.main)['progress_tokens'],second['progress_tokens'])
  for _ in range(3):self.next()
  before=len(self.requests);closed=p.verify_completed_progress(self.main,self.parent['current']['notice_id']);self.assertEqual(closed['progress_tokens'][:2],second['progress_tokens']);self.assertTrue(closed['retired_after_verified_detail_completion']);self.assertEqual(len(self.requests),before)
 def test_own_phase_changed_to_external_manual_hold_is_never_crossed(self):
  self.setup_kind('rates');self.patches();self.next();parent=json.loads(self.main.read_text());parent['waiting_for']='human-investigation';d.nav.write_json(self.main,parent);self.next();self.assertEqual(self.actions,[])
if __name__=='__main__':unittest.main()
