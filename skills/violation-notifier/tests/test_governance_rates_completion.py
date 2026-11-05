"""Real verified source, isolated local completion copies and fake read-only observer. Never live writes."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from datetime import datetime,timedelta
from unittest.mock import patch
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_detail as d,governance_rates_completion as c,governance_capture as capture
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
ROLE=BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca'
FOLDER=ROLE/'rates-recovery'
class CompletionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rm=json.loads((FOLDER/'manifest.json').read_text());cls.rs=json.loads((FOLDER/'state.json').read_text());cls.verified=c.replay.verify_recovery(cls.rm,cls.rs)
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.folder=self.root/'rates-recovery';self.folder.mkdir();self.parent=d.document(self.rm['parent_state']);self.parent_path=self.root/'state.json';self.parent_path.write_bytes(Path(self.rm['parent_state']['path']).read_bytes());self.folder.joinpath('manifest.json').write_bytes((FOLDER/'manifest.json').read_bytes());self.folder.joinpath('state.json').write_bytes((FOLDER/'state.json').read_bytes());self.m=d.document(self.rm['detail_manifest']);self.v=d.inputs(self.m);self.row=self.v['query']['rows'][12];self.reads=0
  p=patch.object(c.recovery,'locations',return_value=(self.parent_path,self.folder));p.start();self.addCleanup(p.stop)
  # Replay dependency was actually validated once above; completion tests isolate
  # the original-prefix/local-intent/fresh-read/append boundary without repeating it.
  p=patch.object(c.replay,'verify_recovery',return_value=self.verified);p.start();self.addCleanup(p.stop)
  owner=self
  class FakeReader:
   def __init__(self,*args):self.s=json.loads(owner.parent_path.read_text());self.file=owner.parent_path
   def save(self):d.nav.write_json(self.file,self.s)
   def observe(self):
    owner.reads+=1;raw=d.document(owner.verified['normal_after']);raw['observed_at']=(datetime.fromisoformat(raw['observed_at'])+timedelta(seconds=owner.reads)).isoformat();path=owner.root/('fresh-'+str(owner.reads)+'.json');d.exclusive(path,raw);self.s['observations'].append(d.ref(path));self.s['last_observation']=d.ref(path);self.save();return raw['tree']
  p=patch.object(c.d,'Runner',FakeReader);p.start();self.addCleanup(p.stop)
 def finish(self):return c.finish(BASE/'detail-inspection-manifest.json',self.rm['parent_state']['sha256'],d.nav.digest(self.folder/'state.json'))
 def test_finish_original_copy_reads_once_appends_one_and_repeat_is_readonly(self):
  original=copy.deepcopy(self.parent);result=self.finish();state=json.loads(self.parent_path.read_text());self.assertEqual(result['cursor'],13);self.assertEqual(state['details'][:12],original['details']);self.assertEqual(state['calls'],original['calls']);self.assertEqual(self.reads,1);self.assertEqual(state['details'][12]['completion_kind'],c.KIND);self.assertTrue(result['detail_progress_changed']);again=self.finish();self.assertTrue(again['already_complete']);self.assertFalse(again['detail_progress_changed']);self.assertEqual(self.reads,1)
 def test_wrong_parent_or_final_hash_rejected_without_ui(self):
  for key in ('parent','final'):
   with self.subTest(key=key),self.assertRaises(ValueError):c.finish(BASE/'detail-inspection-manifest.json','0'*64 if key=='parent' else self.rm['parent_state']['sha256'],'0'*64 if key=='final' else d.nav.digest(self.folder/'state.json'))
  self.assertEqual(self.reads,0);self.assertEqual(json.loads(self.parent_path.read_text())['cursor'],12)
 def test_completed_entry_and_capture_map_keep_mild_ended_period_only(self):
  self.finish();state=json.loads(self.parent_path.read_text());entry=state['details'][12];facts=c.verify_entry(entry,state,self.m,self.v,self.row);mapped=capture.rates_recovered_mapping(self.row,facts,entry,state=state,manifest=self.m,inputs=self.v);self.assertEqual(mapped['actions'],['推荐流量限制（轻度）']);self.assertEqual(mapped['table_effectiveness_status'],'已结束');self.assertEqual(mapped['effective_period']['start'],'2026/10/17 01:57');self.assertEqual(mapped['effective_period']['end'],'2026/10/18 01:57');self.assertTrue(mapped['potential_consequences_excluded_from_actions_and_client_copy']);self.assertNotIn('中等',mapped['disposal_stage_text'])
  for mode in ('facts','prefix','snapshot'):
   wrong=copy.deepcopy(entry);changed=copy.deepcopy(state)
   if mode=='facts':wrong['facts']['effective_statuses']=['已生效']
   elif mode=='prefix':changed['details'][0]['facts']['reason']='伪造'
   else:wrong['recovery_state']['path']=str(self.folder/'state.json')
   with self.subTest(mode=mode),self.assertRaises(ValueError):c.verify_entry(wrong,changed,self.m,self.v,self.row)
 def test_interrupted_fresh_read_resumes_same_local_intent_no_new_source(self):
  with patch.object(c.d.Runner,'observe',side_effect=RuntimeError('read transport unavailable')):
   with self.assertRaisesRegex(RuntimeError,'read transport'):self.finish()
  state=json.loads(self.parent_path.read_text());self.assertEqual(state['phase'],'rates-completion-verification');self.assertEqual(state['cursor'],12);self.assertIn('rates_completion_intent',state);self.finish();self.assertEqual(json.loads(self.parent_path.read_text())['cursor'],13)
if __name__=='__main__':unittest.main()
