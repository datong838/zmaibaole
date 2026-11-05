"""Portable fake bridge only; no UI/RPC, real durable Workflow.once."""
import sys,copy,json,unittest,tempfile,importlib.util
from pathlib import Path
from unittest.mock import patch
R=next(p for p in Path(__file__).resolve().parents if (p/'skills/negative-review-complaints/scripts').is_dir());B=R/'skills/negative-review-complaints/scripts'
sys.path[:0]=[str(R/'skills/negative-review-complaints/scripts'),str(R/'skills/workshop-director/scripts'),str(R/'skills/chrome-dom-export/scripts'),str(R/'skills/douyin-laike-operator/scripts')]
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
h=load('initial_ledger_recovery',B/'initial_ledger_recovery.py');t=load('review_capture_tab',B/'review_capture_tab.py')
class Activation(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.inputs={k:{'path':str(self.root/(k+'.json')),'sha256':'a'*64} for k in ('job','source','profile','envelope')};self.binding={'inputs':self.inputs,'identity':{'company':'test'},'scope':{'tabId':7,'windowId':9,'groupid':'44'},'url':'https://life.douyin.com/p/life_comment/management?groupid=44','original_record_tab':{'tabId':8,'windowId':9,'url':'https://life.douyin.com/p/fulfillsettle/export_records/20101?groupid=44'}};self.active=False;self.focused=True;self.sent=[];self.fail=False
  self.addCleanup(patch.stopall);patch.object(t,'derive_recheck',return_value=self.binding).start()
 def windows(self):
  return [{'windowId':9,'focused':self.focused,'tabs':[{'tabId':7,'windowId':9,'url':self.binding['url'],'allowed':True,'active':self.active},{**self.binding['original_record_tab'],'allowed':True,'active':not self.active}]}]
 def request(self,c):
  self.sent.append(copy.deepcopy(c))
  if c['op']=='tabs':return {'ok':True,'result':self.windows()}
  self.assertEqual(c,{'op':'activate','tabId':7})
  # Intent must already be on disk before the input transport is entered.
  state=json.loads(self.journal().read_text());self.assertEqual(state['calls'][0]['state'],'unknown')
  if self.fail:raise RuntimeError('lost reply')
  self.active=True;self.focused=True;return {'ok':True,'result':{'tabId':7,'windowId':9,'url':self.binding['url'],'active':True,'windowFocused':True}}
 def journal(self):return next((self.root/'.review-recheck-tab-activation').glob('*.json'))
 def runit(self,**kw):return t.ensure_recheck(self.inputs,request=self.request,**kw)
 def test_active_zero_input_and_original_inactive_envelope_unmodified(self):
  self.active=True;before=copy.deepcopy(self.inputs);r=self.runit();self.assertFalse(r['input_attempted']);self.assertEqual(self.sent,[{'op':'tabs'}]);self.assertEqual(self.inputs,before)
 def test_inactive_exact_record_one_activate_then_fresh_and_no_replay(self):
  r=self.runit();self.assertTrue(r['input_attempted']);self.assertEqual([c['op'] for c in self.sent],['tabs','activate','tabs']);self.sent=[];self.assertFalse(self.runit()['input_attempted']);self.assertEqual(self.sent,[{'op':'tabs'}])
 def test_confirmed_then_lost_focus_holds_without_reactivation(self):
  self.runit();self.active=False;self.sent=[]
  with self.assertRaisesRegex(ValueError,'no-replay'):self.runit()
  self.assertEqual(self.sent,[{'op':'tabs'}])
 def test_unknown_without_effect_no_replay_then_readonly_effect_reconcile(self):
  self.fail=True
  with self.assertRaisesRegex(RuntimeError,'lost reply'):self.runit()
  self.assertEqual(json.loads(self.journal().read_text())['calls'][0]['state'],'unknown');self.sent=[]
  with self.assertRaisesRegex(ValueError,'no-replay'):self.runit()
  self.assertEqual(self.sent,[{'op':'tabs'}]);self.active=True;self.sent=[];r=self.runit(readonly=True);self.assertFalse(r['input_attempted']);self.assertEqual(self.sent,[{'op':'tabs'}]);self.assertEqual(json.loads(self.journal().read_text())['calls'][0]['state'],'confirmed')
 def test_readonly_cannot_dispatch_activation(self):
  with self.assertRaisesRegex(ValueError,'readonly-effect'):self.runit(readonly=True)
  self.assertEqual(self.sent,[{'op':'tabs'}])
 def test_wrong_tab_company_url_window_and_duplicate_rejected(self):
  for mode in ('url','window','duplicate','otheractive','missing'):
   w=self.windows()
   if mode=='url':w[0]['tabs'][0]['url']=self.binding['url'].replace('44','45')
   elif mode=='window':w[0]['windowId']=10
   elif mode=='duplicate':w[0]['tabs'].append(copy.deepcopy(w[0]['tabs'][0]))
   elif mode=='otheractive':w[0]['tabs'][1]['url']='https://life.douyin.com/else'
   else:w[0]['tabs'].pop(0)
   with self.subTest(mode=mode),self.assertRaises(ValueError):t.classify(w,self.binding)
 def test_unknown_no_call_rejected(self):
  self.active=True;self.runit();s=json.loads(self.journal().read_text());s['state']='unknown';self.journal().write_text(json.dumps(s));self.sent=[]
  with self.assertRaisesRegex(ValueError,'unknown-without-intent'):self.runit()
  self.assertEqual(self.sent,[{'op':'tabs'}])
 def test_before_once_exception_keeps_preflight_no_call(self):
  with patch.object(t.Activation,'once',side_effect=RuntimeError('before once')):
   with self.assertRaises(RuntimeError):self.runit()
  s=json.loads(self.journal().read_text());self.assertEqual((s['state'],s['calls']),('preflight',[]));self.sent=[];self.assertTrue(self.runit()['input_attempted']);self.assertEqual([x['op'] for x in self.sent],['tabs','activate','tabs'])
 def test_target_active_window_unfocused_can_focus_once(self):
  self.active=True;self.focused=False;self.assertTrue(self.runit()['input_attempted']);self.assertEqual([x['op'] for x in self.sent],['tabs','activate','tabs'])
 def test_readonly_transport_exception_preserves_unknown_input(self):
  self.fail=True
  with self.assertRaises(RuntimeError):self.runit()
  saved=json.loads(self.journal().read_text())['calls'];self.sent=[]
  def failed(c):
   self.sent.append(c);self.assertEqual(c,{'op':'tabs'});raise RuntimeError('readonly failure')
  with self.assertRaisesRegex(RuntimeError,'readonly failure'):t.ensure_recheck(self.inputs,request=failed,readonly=True)
  self.assertEqual(json.loads(self.journal().read_text())['calls'],saved);self.assertEqual(self.sent,[{'op':'tabs'}])
 def test_ports_unknown_operation_holds_before_activation(self):
  ports=load('recheck_activation_test_ports',B/'complaint_execution_ports.py');o=ports.o
  def put(n,v):return o.immutable(self.root/n,v)
  ledger=put('ledger.json',{});job=put('job.json',{'company':'test','groupid':'44','start':'2026-10-19','end_exclusive':'2026-10-20'});source=put('source.json',{});manifest=put('alias/manifest.json',{});put('alias/operation.json',{'state':'unknown-open'})
  unit={'kind':'recheck','start':'2026-10-19','end_exclusive':'2026-10-20','keys':['key']};ctx={'folder':str(self.root/'company'),'company':{'root':str(self.root),'ledger':ledger,'company':'test','groupid':'44'},'artifacts':{'unit_index':0,'units':[unit],'unit_phase':'recheck','unit_artifacts':{'job':job,'source':source,'alias_manifest':manifest,'review_index':0,'recheck_keys':['key']}}}
  port=ports.ProductionPorts(7,1,request=lambda c:(_ for _ in ()).throw(AssertionError('request forbidden')))
  with patch.object(port,'units',return_value=[unit]),patch.object(t,'ensure_recheck',side_effect=AssertionError('activation forbidden')),self.assertRaisesRegex(ValueError,'unknown-no-replay'):port.collect(ctx)
if __name__=='__main__':unittest.main()
