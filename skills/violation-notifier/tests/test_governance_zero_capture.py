"""Portable synthetic double-zero source; no live evidence or business ledger."""
import copy,importlib.util,json,sys,tempfile,unittest
from unittest.mock import patch
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'skills/violation-notifier/scripts'))
import governance_dom as g
import governance_zero_capture as zero
from zero_source_fixtures import Evidence,q as query
def read(p):return json.loads(p.read_text())
class DoubleZero(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.e=Evidence(self,self.root);self.job=self.e.job;self.state,self.raw=self.e.original_records();state=read(self.state);self.events=self.e.events
  runner=query.Runner(self.job,state['tab_id'],self.state,query.nav.VERSION,self.e.invoke);runner.reconcile_records_zero(query.nav.digest(self.state),state['last_observation']['sha256'])
  self.refs={'job':zero.d.ref(self.e.jobpath),'center_query':zero.d.ref(self.e.center_query()),'records_query':zero.d.ref(self.state)}
 def test_prepare_build_validate_independent_synthetic_double_zero(self):
  ref=zero.prepare(self.refs['job']['path'],self.refs['center_query']['path'],self.refs['records_query']['path'],self.root/'profile.json',self.root/'manifest.json');out=self.root/'capture.json';result=zero.build(ref['path'],out);self.assertEqual(zero.validate(out),result);self.assertEqual(result['analysis']['total'],0);self.assertEqual(result['records']['total'],0);self.assertTrue(result['source_contract']['detail_not_applicable']);self.assertFalse(result['source_contract']['all_notice_details_verified']);self.assertNotIn('click',[c['op'] for c in self.events])
 def test_unknown_or_altered_query_source_refused(self):
  original=read(self.state)
  for mode in ('unknown','gid','scope','pending','page'):
   q=copy.deepcopy(original)
   if mode=='unknown':q['calls'][-1]['state']='unknown'
   if mode=='gid':q['fingerprint']='fake'
   if mode=='scope':q['tab_id']+=1
   if mode=='pending':q['needs_changed_tree']=q['last_observation']
   if mode=='page':q['pages'][0]['total']=1
   self.state.write_text(json.dumps(q,ensure_ascii=False));refs={**self.refs,'records_query':zero.d.ref(self.state)}
   with self.subTest(mode=mode),self.assertRaises(ValueError):zero.derive_profile(refs)
  self.state.write_text(json.dumps(original,ensure_ascii=False))
 def test_forged_profile_and_flags_only_json_cannot_validate(self):
  ref=zero.prepare(self.refs['job']['path'],self.refs['center_query']['path'],self.refs['records_query']['path'],self.root/'profile.json',self.root/'manifest.json');m=zero.d.document(ref);profile=self.root/'profile.json';value=read(profile);value['center_zero']['start']='2026-10-15';profile.write_text(json.dumps(value));m['inputs']['profile']=zero.d.ref(profile)
  with self.assertRaisesRegex(ValueError,'profile-derived-content-conflict'):zero.inputs(m)
  out=self.root/'fake.json';out.write_text(json.dumps({'capture_schema':zero.SCHEMA,'analysis_zero':True,'records_zero':True}))
  with self.assertRaisesRegex(ValueError,'manifest-reference-required'):zero.validate(out)
 def test_formal_common_validate_dispatch_and_live_backend_workflow_gate(self):
  sys.path.insert(0,str(ROOT/'skills/daily-comment-stats/scripts'))
  spec=importlib.util.spec_from_file_location('isolated_zero_workflow',ROOT/'skills/violation-notifier/scripts/workflow.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w);w.PROJECT=ROOT;w.SKILL=ROOT/'skills/violation-notifier'
  ref=zero.prepare(self.refs['job']['path'],self.refs['center_query']['path'],self.refs['records_query']['path'],self.root/'profile.json',self.root/'manifest.json');out=self.root/'capture.json';value=zero.common.build(ref['path'],out);self.assertEqual(zero.common.validate(out),value)
  ledger=self.root/'synthetic-ledger';ledger.mkdir();
  with patch.object(w,'route',return_value=('123','测试路由群')):state=w.initialize(ledger,self.job['company'],'2026-10-22','2026-10-16',mode='fixture',backend='local-dom-bridge')
  state['mode']='development'
  with patch.object(w,'shanghai_today',return_value=date(2026,10,22)),patch.object(zero.common,'validate',wraps=zero.common.validate) as checked:
   result=w.ingest(ledger,state,out,'2026-10-22');self.assertEqual(result['batches']['2026-10-16_2026-10-21']['status'],'zero_verified');checked.assert_called_once_with(out)
  fake=self.root/'fake.json';fake.write_text(json.dumps({k:v for k,v in value.items() if k!='capture_manifest'}));state['batches']={}
  with patch.object(w,'shanghai_today',return_value=date(2026,10,22)),self.assertRaisesRegex(ValueError,'manifest-reference-required'):w.ingest(ledger,state,fake,'2026-10-22')
 def test_completed_synthetic_refs_parse_without_writes(self):
  ref=self.refs;v=zero.sources(ref);self.assertEqual(v['records_zero']['total'],0);self.assertTrue(v['center_zero']['analysis_zero_verified'])
if __name__=='__main__':unittest.main()
