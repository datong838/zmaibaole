"""Portable TEMP bindings using saved public DOM; source/profile deep validators
are mocked only in synthetic mutation tests. Actual full replay is separate audit.
"""
import copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parent;R=H.parents[2];D=R/'skills/violation-notifier/scripts';sys.path[:0]=[str(D),str(R/'skills/chrome-dom-export/scripts')]
spec=importlib.util.spec_from_file_location('candidate_records_nav',R/'skills/workshop-director/scripts/records_navigation_progress.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
import governance_detail as d,prepare_records_profile as p
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
  self.docs={k:json.loads((H/'fixtures/records-navigation'/f'{k}.json').read_text()) for k in ('source','profile','job','query','observation')}
  self.source=self.put('source.json',self.docs['source']);self.job=self.put('job.json',self.docs['job']);self.baseline=self.put('baseline.json',self.docs['observation']);self.docs['query']['pages'][0]['observation']=self.baseline;self.query=self.put('query.json',self.docs['query'])
  meta=self.docs['profile']['derivation'];meta.update(source=self.source,job=self.job,query=self.query);self.profile=self.put('profile.json',self.docs['profile'])
  self.path=self.root/'.records-region-navigation'/self.source['sha256']/'state.json';self.obs=self.put(str(self.path.parent.relative_to(self.root)/'evidence/0000.json'),self.docs['observation'])
  self.state={'binding':{'schema':'records-region-navigation-v1','source':self.source,'profile':self.profile,'job':self.job,'query':self.query,'tab_id':meta['tab_id'],'window_id':meta['window_id']},'operations':[],'observations':[self.obs],'last_observation':self.obs,'business_progress_changed':False};self.save()
  self.addCleanup(patch.stopall);patch.object(p.source_api,'validate',return_value=self.docs['source']).start();patch.object(p,'validate',return_value=self.docs['profile']).start()
 def put(self,name,obj):
  f=self.root/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(json.dumps(obj,ensure_ascii=False));return {'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 def save(self):self.path.parent.mkdir(parents=True,exist_ok=True);self.path.write_text(json.dumps(self.state,ensure_ascii=False))
 def verify(self,**kw):self.save();return m.verify(self.state,self.path,role=kw.get('role','violation_operator'),records_directory=D)
 def mutate_obs(self,fn):
  raw=copy.deepcopy(self.docs['observation']);fn(raw);self.obs=self.put(str(self.path.parent.relative_to(self.root)/'evidence/0000.json'),raw);self.state['observations']=[self.obs];self.state['last_observation']=self.obs
 def test_zero_input_no_progress_and_no_constructor(self):
  result=self.verify();self.assertEqual(result['tokens'],{});self.assertFalse(result['readonly_navigation']['observations_are_progress'])
 def test_wrong_role_rejects(self):
  with self.assertRaises(ValueError):self.verify(role='complaint_operator')
 def test_any_operation_unknown_confirmed_or_complete_requires_other_monitor(self):
  for state in ('unknown','confirmed'):
   self.state['operations']=[{'state':state}]
   with self.assertRaisesRegex(ValueError,'operation-unresolved'):self.verify()
 def test_copy_wrong_canonical_path_rejects(self):
  self.save();other=self.root/'copy.json';other.write_bytes(self.path.read_bytes())
  with self.assertRaisesRegex(ValueError,'journal-path'):m.verify(self.state,other,role='violation_operator',records_directory=D)
 def test_changed_source_and_false_hash_reject(self):
  Path(self.source['path']).write_text('{}')
  with self.assertRaisesRegex(ValueError,'evidence-changed'):self.verify()
 def test_window_group_provider_and_business_changes_reject(self):
  cases=[lambda raw:raw['tab'].update(windowId=1),lambda raw:raw['tab'].update(url='https://life.douyin.com/p/governance/violation_list?groupid=1'),lambda raw:next(n for n in d.g.nodes(raw['tree']) if 'Profile-index-module__title--' in n.get('attributes',{}).get('class','')).update(name='服务商1'),lambda raw:next(n for n in d.g.nodes(raw['tree']) if n.get('tag')=='td').update(name='changed')]
  for fn in cases:
   self.mutate_obs(fn)
   with self.assertRaises(ValueError):self.verify()
 def test_invisible_card_uses_proven_entry_and_current_provider(self):
  def remove(raw):
   def rec(n):n['children']=[c for c in n.get('children',[]) if 'UserCard-index-module__outer--' not in c.get('attributes',{}).get('class','')];[rec(c) for c in n['children']]
   rec(raw['tree']['root'])
  self.mutate_obs(remove);result=self.verify();self.assertEqual(result['readonly_navigation']['visible_full_identity_per_observation'],[False]);self.assertEqual(result['readonly_navigation']['full_identity_source'],'verified-source-query-entry')
 def test_normal_complete_scroll_full_verifier_and_noop(self):
  from datetime import datetime,timedelta
  before=self.obs;raw=copy.deepcopy(self.docs['observation']);t=datetime.fromisoformat(raw['observed_at']);raw['observed_at']=(t+timedelta(seconds=2)).isoformat();after=self.put(str(self.path.parent.relative_to(self.root)/'evidence/0001.json'),raw);self.state['observations'].append(after);self.state['last_observation']=after
  page=d.normal_page(raw['tree'],self.docs['job'],self.docs['query']);row=page['rows'][0];node=d.g.one([n for n in d.g.nodes(raw['tree']) if n.get('selector')==row['selector']],'synthetic-row');result={'version':d.nav.VERSION,'scrolled':{'selector':node['selector'],'tag':'tr'}}
  op={'key':'synthetic-scroll-key','request':{'action':'row','page':None,'notice_id':row['notice_id']},'state':'complete','before':before,'before_page':page['page'],'intent_at':(t+timedelta(microseconds=1)).isoformat(),'command':{'op':'scroll','locator':{'by':'selector','value':row['selector']},'tabId':self.state['binding']['tab_id']},'raw_reply':{'ok':True,'result':result},'result':result,'response_at':(t+timedelta(seconds=1)).isoformat(),'after':after,'completed_at':(t+timedelta(seconds=3)).isoformat()};self.state['operations']=[op]
  self.assertEqual(self.verify()['tokens'],{})
  self.state['operations'].append({'key':'synthetic-noop-key','request':{'action':'page','page':page['page'],'notice_id':None},'state':'complete','before':after,'before_page':page['page'],'intent_at':(t+timedelta(seconds=4)).isoformat(),'command':None});self.assertEqual(self.verify()['tokens'],{})
 def test_risk_and_truncated_refuse(self):
  self.mutate_obs(lambda raw:raw['tree'].update(truncated=True))
  with self.assertRaises(ValueError):self.verify()
  self.mutate_obs(lambda raw:raw['tree']['root'].update(name='风险验证'))
  with self.assertRaises(ValueError):self.verify()
if __name__=='__main__':unittest.main()
