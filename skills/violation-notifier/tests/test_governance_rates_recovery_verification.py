"""Pure replay of actual final recovery plus in-memory/temp-file negative cases; no UI."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_rates_recovery_verification as verify
import governance_rates_recovery as runtime
import governance_detail as d
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
FOLDER=BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca/rates-recovery'
class VerificationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  # Revalidate the immutable original twelve/source once. Negative cases below
  # isolate new replay checks rather than repeatedly parsing the same prefix.
  cls.validated_source=runtime.source_inputs(json.loads((FOLDER/'manifest.json').read_text()))
 def setUp(self):
  guard=patch.object(runtime,'source_inputs',return_value=self.validated_source);guard.start();self.addCleanup(guard.stop)
  self.manifest=json.loads((FOLDER/'manifest.json').read_text());self.state=json.loads((FOLDER/'state.json').read_text());self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
 def test_actual_final_replay_is_pure_and_does_not_complete_notice(self):
  with patch.object(runtime.Runner,'__init__',side_effect=AssertionError('no runtime/bridge')):result=verify.verify_recovery(self.manifest,self.state)
  self.assertEqual(result['original_cursor'],12);self.assertEqual(result['notice_id'],'ZS202610174748574044');self.assertEqual(result['restored_page']['page'],2);self.assertEqual(len(result['restored_page']['rows']),6);self.assertEqual([p['page'] for p in result['center_pages']],[1,2]);self.assertFalse(result['detail_completed']);self.assertFalse(result['ui_used']);self.assertEqual(result['arrow_return_effect'],'not-observed')
 def test_wrapper_unknown_wrong_purpose_reply_or_omitted_page_action_rejected(self):
  for mode in ('unknown','purpose','reply','omit_page','final_row','phase','child_missing'):
   state=copy.deepcopy(self.state)
   if mode=='unknown':state['calls'][0]['state']='unknown'
   elif mode=='purpose':state['calls'][0]['purpose']='unreviewed'
   elif mode=='reply':state['calls'][1]['result']['clicked']['name']='去管理门店'
   elif mode=='omit_page':state['calls']=state['calls'][:2]
   elif mode=='final_row':state['restored_page']['rows'][0]['disposal']='伪造'
   elif mode=='phase':state['phase']='complete'
   else:state['filter_final_snapshots']={}
   with self.subTest(mode=mode),self.assertRaises((ValueError,KeyError)):verify.verify_recovery(self.manifest,state)
 def test_child_commands_unknown_result_and_range_state_replayed_not_flags(self):
  m,v,parent,row=runtime.source_inputs(self.manifest);job=v['job'];window=d.document(parent['last_observation'])['tab']['windowId'];original=d.document(self.state['filter_final_snapshots']['center-range'])
  for mode in ('unknown','command','reply','intent','phase','finalref'):
   child=copy.deepcopy(original)
   if mode=='unknown':child['calls'][0]['state']='unknown'
   elif mode=='command':child['calls'][0]['command']['locator']['value']='#unreviewed'
   elif mode=='reply':child['calls'][0]['result']['clicked']['name']='different'
   elif mode=='intent':child['calls'][0]['intent_at']='2000-01-01T00:00:00+00:00'
   elif mode=='phase':child['phase']='profile-required-but-unverified'
   else:child['last_observation']=child['observations'][0]
   path=self.root/(mode+'.json');d.exclusive(path,child)
   with self.subTest(mode=mode),self.assertRaises((ValueError,KeyError)):verify.verify_filter(d.ref(path),runtime.g.CENTER,job,m['tab_id'],window,v['query'])
 def settling_state(self,purpose):
  from datetime import datetime
  state=copy.deepcopy(self.state);call=next(c for c in state['calls'] if c['purpose']==purpose);i=state['observations'].index(call['before']);before=d.document(call['before']);after=d.document(state['observations'][i+1]);start=datetime.fromisoformat(call['intent_at']);end=datetime.fromisoformat(after['observed_at']);before['observed_at']=(start+(end-start)/2).isoformat();p=self.root/(purpose+'.json');d.exclusive(p,before);state['observations'].insert(i+1,d.ref(p));return state
 def test_same_source_async_center_and_records_settling_is_valid(self):
  for purpose in ('center-top10-next-page','center-records-entry'):
   with self.subTest(purpose=purpose):result=verify.verify_recovery(self.manifest,self.settling_state(purpose));self.assertEqual(result['restored_page']['page'],2)
 def test_effect_cannot_be_searched_across_next_command_boundary(self):
  state=copy.deepcopy(self.state);effect=state['center_pages'][1]['observation'];state['observations'].remove(effect)
  with self.assertRaisesRegex(ValueError,'effect-outside-action-window'):verify.verify_recovery(self.manifest,state)
 def test_child_snapshot_hash_and_location_are_mandatory(self):
  for mode in ('hash','path'):
   state=copy.deepcopy(self.state)
   if mode=='hash':state['filter_final_snapshots']['center-range']['sha256']='0'*64
   else:
    path=self.root/'copied.json';d.exclusive(path,d.document(state['filter_final_snapshots']['center-range']));state['filter_final_snapshots']['center-range']=d.ref(path)
   with self.subTest(mode=mode),self.assertRaises(ValueError):verify.verify_recovery(self.manifest,state)
if __name__=='__main__':unittest.main()
