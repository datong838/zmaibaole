"""Isolated fake ports; no UI, no production journal writes."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_stop_loss_integration as flow
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
ROLE=BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca'
class Ports:
 def __init__(self):self.calls=[];self.failure=None;self.bad=False;self.block=False;self.reads=0
 def assert_source(self,b,s):
  if self.block:raise ValueError('nested unknown')
 def verify(self,step,r,b,receipts):
  if self.bad:raise ValueError('fresh effect not verified')
 def readonly_reconcile(self,b,s):self.reads+=1;return {'unknown':True,'only_read':True}
 def __getattr__(self,name):
  if name not in flow.EFFECTS:raise AttributeError(name)
  def call(b,receipts):
   self.calls.append(name)
   if self.failure==name:raise RuntimeError('lost outcome')
   return {'effect':flow.EFFECTS[name],'binding_sha256':flow.digest(b),'route_contract':flow.DIRECT,'arrow_issued':False}
  return call
class IntegrationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'state.json';self.ports=Ports();self.m={'inputs':{'query':{'path':'/mock/query.json','sha256':'abc'}}};self.v={'job':{}};self.parent={'manifest':self.m,'phase':'read-detail','cursor':0,'current':{'notice_id':'n','normal_before':{'path':'/mock/before','sha256':'x'}},'details':[],'calls':[]};self.binding={'kind':'rates','notice_id':'n','cursor':0,'prefix_sha256':flow.digest([])}
  p=patch.object(flow,'location',return_value=self.path);p.start();self.addCleanup(p.stop)
  p=patch.object(flow,'detect',side_effect=lambda *a:copy.deepcopy(self.binding));p.start();self.addCleanup(p.stop)
 def instance(self,path=None):return flow.Flow(self.m,self.v,self.parent,self.ports,path)
 def test_both_template_sequences_do_not_dispatch_arrow_or_arbitrary_operation(self):
  for kind in ('rates','product'):
   self.binding['kind']=kind
   if self.path.exists():self.path.unlink()
   self.ports.calls=[];f=self.instance()
   for _ in flow.STEPS[kind]:f.tick(self.parent)
   self.assertTrue(f.s['complete']);self.assertEqual(self.ports.calls,list(flow.STEPS[kind]));self.assertFalse(any('arrow' in c for c in self.ports.calls));f.tick(self.parent);self.assertEqual(len(self.ports.calls),len(flow.STEPS[kind]))
 def test_lost_outcome_durable_unknown_never_replays_or_advances_on_normal_route(self):
  self.ports.failure='rates_sidebar_once';f=self.instance();f.tick(self.parent)
  with self.assertRaises(RuntimeError):f.tick(self.parent)
  self.ports.failure=None;f=self.instance();before=len(self.ports.calls);f.tick(self.parent);result=f.reconcile();self.assertTrue(result['only_read']);self.assertEqual(before,len(self.ports.calls));self.assertEqual(f.s['phase'],'rates_sidebar_once');self.assertEqual(f.s['calls'][-1]['state'],'unknown')
 def test_explicit_parent_hold_unknown_and_nested_unknown_zero_operations(self):
  for field,value in (('hold',True),('waiting_for','human-review'),('calls',[{'state':'unknown'}])):
   f=self.instance();p=copy.deepcopy(self.parent);p[field]=value;f.tick(p);self.assertEqual(self.ports.calls,[])
  self.ports.block=True
  with self.assertRaisesRegex(ValueError,'nested unknown'):self.instance().tick(self.parent)
  self.assertEqual(self.ports.calls,[])
 def test_pending_cannot_skip_binding_or_direct_no_arrow_contract(self):
  f=self.instance();f.s['phase']='rates_read_center';f.save()
  for result in ({'effect':'pending'}, {'effect':'pending','binding_sha256':flow.digest(self.binding),'route_contract':flow.DIRECT,'arrow_issued':True}):
   f.s['calls']=[];f.s.pop('hold',None);f.s.pop('waiting_for',None);f.save()
   with patch.object(self.ports,'rates_read_center',return_value=result),self.assertRaises(ValueError):f.tick(self.parent)
   self.assertEqual(f.s['calls'][-1]['state'],'unknown')
 def test_copied_journal_changed_source_and_unverified_effect_refuse(self):
  f=self.instance()
  with self.assertRaisesRegex(ValueError,'canonical'):self.instance(self.path.parent/'copied.json')
  p=copy.deepcopy(self.parent);p['current']['notice_id']='other'
  with self.assertRaisesRegex(ValueError,'parent-source'):f.tick(p)
  self.ports.bad=True
  with self.assertRaisesRegex(ValueError,'not verified'):f.tick(self.parent)
  self.assertEqual(f.s['calls'][-1]['state'],'unknown')
class ActualDetectionTests(unittest.TestCase):
 def test_original_product_and_rates_archives_are_parsed_not_adopted_or_written(self):
  m=json.loads((BASE/'detail-inspection-manifest.json').read_text());v=flow.d.inputs(m)
  for glob,kind in (('stop-loss-original-*.json','product'),('rates-stop-loss-original-*.json','rates')):
   originals=list(ROLE.glob(glob));self.assertTrue(originals)
   for path in originals:
    before=path.read_bytes();p=json.loads(before);p.pop('hold',None);p.pop('waiting_for',None);b=flow.detect(p,m,v);self.assertEqual(b['kind'],kind);self.assertEqual(path.read_bytes(),before)
if __name__=='__main__':unittest.main()
