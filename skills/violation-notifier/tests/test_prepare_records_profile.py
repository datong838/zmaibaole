"""Actual two-page saved DOM. Source-assembly itself is independently replayed;
unit cases isolate profile/row/scope derivation instead of repeating its 100s replay.
"""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import prepare_records_profile as p
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
class ProfileTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.source=p.d.ref(BASE/'complete-governance-source.json');cls.job=p.d.ref(BASE/'navigation-job.json');cls.query=p.d.ref(BASE/'records-range-query-v9.json');cls.src=p.d.document(cls.source);cls.q=p.d.document(cls.query)
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);mock=patch.object(p.source_api,'validate',side_effect=lambda path:json.loads(Path(path).read_text()));self.validator=mock.start();self.addCleanup(mock.stop)
 def write(self,name,value):path=self.root/name;p.d.exclusive(path,value);return p.d.ref(path)
 def profile(self):return p.derive(self.source,self.job,self.query)
 def test_actual_two_pages_total16_pinned_profile_and_existing_page_inputs(self):
  result=p.prepare(self.source,self.job,self.query,self.root/'profile.json');self.assertEqual(result['status'],'DOM-derived-ready');self.assertEqual(result['pages'],2);self.assertEqual(result['total'],16);self.assertFalse(result['screenshot_accepted']);profile=p.d.document(result['profile']);self.assertEqual([len(x['notice_ids']) for x in profile['derivation']['pages']],[10,6])
  for i,page in enumerate(self.q['pages']):
   before_path=list(sys.path);inputs=p.fc.page_inputs(self.source,page['observation'],result['profile']);self.assertEqual(sys.path,before_path);self.assertEqual(inputs['scope']['page'],i+1);self.assertEqual(len(inputs['scope']['page_rows']),10 if i==0 else 6);self.assertEqual(inputs['scope']['last_page'],i==1)
 def test_prepare_runs_complete_source_gate_once_runtime_replays_only_scope(self):
  result=p.prepare(self.source,self.job,self.query,self.root/'profile.json');self.assertEqual(self.validator.call_count,1)
  for page in self.q['pages']:p.fc.page_inputs(self.source,page['observation'],result['profile'])
  self.assertEqual(self.validator.call_count,1)
 def test_other_company_group_date_or_truncated_fresh_observation_refuses(self):
  profile=self.write('profile.json',self.profile())
  for mode in ('group','date','truncated','subject','headers'):
   raw=p.d.document(self.q['pages'][0]['observation'])
   if mode=='group':raw['tab']['url']=raw['tab']['url'].replace('1767942028615694','1234567890')
   elif mode=='date':p.g.date_input(raw['tree'])['attributes']['value']='2026/10/15 ～ 2026/10/20'
   elif mode=='truncated':raw['tree']['truncated']=True
   elif mode=='headers':next(n for n in p.g.nodes(raw['tree']) if n.get('tag')=='th')['name']='错误表头'
   else:next(n for n in p.g.nodes(raw['tree']) if 'name-iUMfRa' in p.g.cls(n) and not n.get('children'))['name']='其他公司门店'
   with self.subTest(mode=mode),self.assertRaises(ValueError):p.fc.page_inputs(self.source,self.write(mode+'.json',raw),profile)
 def test_row_id_moved_from_first_cell_and_incomplete_cells_refuse(self):
  profile=self.write('profile.json',self.profile())
  for mode in ('id','cells'):
   raw=p.d.document(self.q['pages'][0]['observation']);row=next(n for n in p.g.nodes(raw['tree']) if n.get('tag')=='tr' and 'governance_merchant-Table-Row' in p.g.cls(n))
   if mode=='id':row['children'][0]['name']='一般 缺少ID';row['children'][1]['name']+=' ID:202610204779150548'
   else:row['children'].pop()
   with self.subTest(mode=mode),self.assertRaises(ValueError):p.fc.page_inputs(self.source,self.write(mode+'.json',raw),profile)
 def test_forged_selector_status_or_rawref_rejected_by_mechanical_rederive(self):
  for mode in ('selector','status','rawref'):
   value=self.profile()
   if mode=='selector':value['records']['root']['selector']='#invented-table'
   elif mode=='status':value['status']='live-validated'
   else:value['derivation']['pages'][0]['observation']['sha256']='0'*64
   with self.subTest(mode=mode),self.assertRaises(ValueError):p.fc.page_inputs(self.source,self.q['pages'][0]['observation'],self.write(mode+'.json',value))
 def test_fixture_capture_wrong_company_or_pinned_checksum_not_accepted(self):
  for mode in ('fixture','company'):
   source=copy.deepcopy(self.src)
   if mode=='fixture':source['capture_schema']='fixture'
   else:source['company']='其他公司'
   with self.subTest(mode=mode),self.assertRaises(ValueError):p.derive(self.write(mode+'.json',source),self.job,self.query)
  with self.assertRaises(ValueError):p.derive({**self.source,'sha256':'0'*64},self.job,self.query)
if __name__=='__main__':unittest.main()
