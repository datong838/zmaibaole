"""Synthetic send-order generation only. No business state, UI, or messages."""
import copy,hashlib,importlib.util,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/daily-comment-stats/scripts'))
P=ROOT/'skills/violation-notifier/scripts/workflow.py'
spec=importlib.util.spec_from_file_location('formal_send_reference_workflow',P)
w=importlib.util.module_from_spec(spec);sys.modules[spec.name]=w;spec.loader.exec_module(w)
class References(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.counter=0
 def ref(self,text):
  self.counter+=1;p=self.root/str(self.counter);p.write_text(text);return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 def build(self,counts=(8,8,11,17,13,19,20),backend='screen-capture-kit-dom-region'):
  frames=[]
  for i,count in enumerate(counts):
   frames.append({'file':self.ref('image-'+str(i)),'metadata':self.ref('metadata-'+str(i)),'notice_ids':['n'+str(i)],'frame_mode':'rows','page':1,'references':[self.ref('prefix/manual-'+str(i)+'-'+str(n)) for n in range(count)]})
  manifest=self.ref(json.dumps({'capture_backend':backend}))
  chain={'manifest':manifest,'frames':frames,'chain_id':'same-chain','notice_ids':['n'+str(i) for i in range(len(frames))],'source_sha256':None,'visibility_policy':'notice-five-business-cells-v1','capture_backend':backend,'whole_window':False,'region_only':True,'viewport_only':False}
  source=self.ref('source');chain['source_sha256']=source['sha256'];text=self.ref('copy')
  b={'start':'2026-10-16','end_exclusive':'2026-10-21','source':source,'total':len(frames),'records':[{'notice_id':v} for v in chain['notice_ids']],'copy':text,'copy_evidence':text,'artifacts':{'source_sha256':source['sha256'],'files':[]},'screenshots':[],'screenshot_chains':[chain]}
  state={'company':'synthetic','groupid':'123','mode':'development','browser_backend':'local-dom-bridge','batches':{'batch':b}}
  checked={'chain_id':chain['chain_id'],'notice_ids':chain['notice_ids'],'entries':[{'image':copy.deepcopy(f['file']),**{k:copy.deepcopy(f[k]) for k in ('metadata','notice_ids','frame_mode','page','references')}} for f in frames]}
  return state,chain,checked
 def orders(self,state,checked):
  fake=types.ModuleType('region_frame_capture');fake.validate_chain=lambda *a,**k:checked
  with patch.dict(sys.modules,{'region_frame_capture':fake}),patch.object(w,'validate_artifact_coverage',lambda *_:None):return w.send_orders(state,'batch')
 def test_actual_variable_cardinalities_and_old_six_eight_remain_valid(self):
  for counts in ((8,8,11,17,13,19,20),(6,8)):
   state,chain,checked=self.build(counts);orders=self.orders(state,checked)
   self.assertEqual(len([o for o in orders if o['part'].startswith('source_list_screenshot:')]),len(counts));self.assertTrue(all(o['target']=='测试群请忽略' for o in orders))
 def test_registered_reference_delete_append_reorder_replace_rejected(self):
  for change in ('delete','append','order','replace'):
   state,chain,checked=self.build((11,));refs=chain['frames'][0]['references']
   if change=='delete':refs.pop()
   elif change=='append':refs.append(self.ref('additional'))
   elif change=='order':refs.reverse()
   else:refs[0]=self.ref('different valid file')
   with self.subTest(change=change),self.assertRaisesRegex(ValueError,'native-chain-registered-frame-changed'):self.orders(state,checked)
 def test_actual_reference_change_rejected(self):
  state,chain,checked=self.build((17,));checked['entries'][0]['references'].pop()
  with self.assertRaisesRegex(ValueError,'native-chain-registered-frame-changed'):self.orders(state,checked)
 def test_same_reference_sha_but_tampered_file_rejected(self):
  state,chain,checked=self.build((20,));Path(chain['frames'][0]['references'][9]['path']).write_text('tampered')
  with self.assertRaisesRegex(ValueError,'evidence-changed'):self.orders(state,checked)
 def test_full_validator_failure_not_bypassed(self):
  state,chain,checked=self.build((11,));fake=types.ModuleType('region_frame_capture')
  def reject(*a,**k):raise ValueError('synthetic-original-full-validation-failed')
  fake.validate_chain=reject
  with patch.dict(sys.modules,{'region_frame_capture':fake}),patch.object(w,'validate_artifact_coverage',lambda *_:None),self.assertRaisesRegex(ValueError,'original-full-validation-failed'):w.send_orders(state,'batch')
 def test_legacy_nonregion_fixed_five_and_historical_send_rejection_unchanged(self):
  for count,error in ((6,'frame-chain-send-proof-incomplete'),(5,'region-only-final-evidence-required-historical-viewport')):
   state,chain,checked=self.build((count,),backend=None)
   with self.assertRaisesRegex(ValueError,error):self.orders(state,checked)
if __name__=='__main__':unittest.main()
