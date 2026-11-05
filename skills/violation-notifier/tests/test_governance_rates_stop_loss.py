"""Actual three-rates stop-loss DOM and fake read-only staging, no live UI."""
import copy,json,sys,tempfile,unittest,subprocess,os
from pathlib import Path
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_detail as d,governance_rates_stop_loss as rates
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
DIR=BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca'
class RatesTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.m=json.loads((BASE/'detail-inspection-manifest.json').read_text());self.v=d.inputs(self.m);self.row=self.v['query']['rows'][12];self.raw=json.loads((DIR/'state-evidence/0059.json').read_text());before=d.document(d.ref(DIR/'state-evidence/0058.json'));command={**self.row['detail'],'tabId':995698279};target=next(n for n in d.g.nodes(before['tree']) if n['selector']==command['locator']['value']);self.call={'state':'confirmed','before':d.ref(DIR/'state-evidence/0058.json'),'command':command,'result':{'kind':'navigation','version':d.nav.VERSION,'clicked':target}}
 def test_actual_notice_shop_id_time_mapping_and_completed_disposal(self):
  facts,command=rates.parse(self.raw,self.row,self.call,self.v['job']);self.assertEqual(facts['reason'],'三率超标');self.assertEqual(facts['detail_reason'],'门店差评率、商责退单率超标');self.assertEqual(facts['notification_time'],'2026/10/17 01:57');self.assertEqual(facts['object_id'],'7563983099585447978');self.assertEqual(facts['disposals'],['推荐流量限制（轻度）']);self.assertEqual(facts['effective_statuses'],['已结束']);self.assertEqual(facts['effective_period']['end'],'2026/10/18 01:57');self.assertEqual(facts['potential_consequences'][0]['text'],'推荐流量限制（中等）');self.assertFalse(facts['potential_consequences'][0]['execution_observed']);self.assertTrue(facts['potential_consequences'][0]['excluded_from_actions_and_client_copy']);self.assertNotIn('中等',facts['public_recommendation']);self.assertNotIn('1.85',facts['public_recommendation']);self.assertEqual(command['locator']['value'],'#root > div > div:nth-of-type(1) > div:nth-of-type(1)');self.assertEqual(command['kind'],'navigation')
 def test_other_query_notice_period_object_or_arrow_shape_refuses(self):
  for mode in ('query','id','period','object','title','arrow','open','status','advice'):
   raw=copy.deepcopy(self.raw);row=copy.deepcopy(self.row);call=copy.deepcopy(self.call);nodes=d.g.nodes(raw['tree'])
   if mode=='query':raw['tab']['url']+='&EnterFrom=home_violation_center'
   elif mode=='id':next(n for n in nodes if n.get('attributes',{}).get('class')=='flex items-center text-[14px] leading-[22px] text-[#6C737A]')['name']='通知时间 2026/10/17 01:57 通知单ID other'
   elif mode=='period':next(n for n in nodes if n.get('attributes',{}).get('class')=='mt-[4px] leading-[18px] text-[14px] text-[#a8abb2]')['name']='周期：2026/10/18 01:57 ~ 2026/10/19 01:57'
   elif mode=='object':row['object']='different'
   elif mode=='title':next(n for n in nodes if n.get('name')==rates.TITLE and not n.get('children'))['name']='其他'
   elif mode=='arrow':next(n for n in nodes if n.get('attributes',{}).get('class')==rates.ARROW_CLASS)['children'][0]['tag']='button'
   elif mode=='open':call['state']='unknown'
   elif mode=='status':next(n for n in nodes if n.get('tag')=='span' and n.get('name')=='已结束')['name']='已生效'
   else:next(n for n in nodes if n.get('attributes',{}).get('class')=='my-[8px] is__content-TWHNZz' and n.get('name','').startswith('建议您查看'))['children']=[{'tag':'input','name':'不读取表单'}]
   with self.subTest(mode=mode),self.assertRaises(ValueError):rates.parse(raw,row,call,self.v['job'])
 def runner(self):
  r=object.__new__(rates.Runner);r.manifest=self.m;r.v=copy.deepcopy(self.v);r.v['query']['rows']=[self.row];r.job=self.v['job'];r.tab=995698279;r.file=self.root/'state.json';r.s={'manifest':self.m,'fingerprint':d.nav.tag(r.job),'phase':'read-detail','cursor':0,'details':[],'calls':[self.call],'current':{'notice_id':self.row['notice_id'],'normal_before':self.call['before']},'last_observation':d.ref(DIR/'state-evidence/0059.json'),'observations':[]};r.save();self.requests=[]
  def observe():
   path=self.root/('fresh-'+str(len(r.s['observations']))+'.json');d.exclusive(path,self.raw);r.s['last_observation']=d.ref(path);r.s['observations'].append(d.ref(path));r.save();return self.raw['tree']
  r.observe=observe;r.request=lambda cmd:self.requests.append(cmd);return r
 def test_stage_archives_bytes_fresh_checks_no_action_no_advance(self):
  r=self.runner();original=r.file.read_bytes();sha=d.nav.digest(r.file);obs=r.s['last_observation']['sha256'];r.stage(sha,obs);self.assertEqual(Path(r.s['rates_stop_loss_stage']['original_state']['path']).read_bytes(),original);self.assertEqual(r.s['phase'],'rates-stop-loss-return-ready');self.assertFalse(r.s['current']['return_enabled']);self.assertEqual(r.s['cursor'],0);self.assertEqual(r.s['details'],[]);self.assertEqual(self.requests,[]);r.stage(sha,obs);self.assertEqual(self.requests,[])
 def test_stage_wrong_hash_and_fresh_change_refuse_without_click(self):
  r=self.runner()
  with self.assertRaises(ValueError):r.stage('0'*64,r.s['last_observation']['sha256'])
  self.raw['tab']['url']+='&bad=1'
  with self.assertRaises(ValueError):r.stage(d.nav.digest(r.file),r.s['last_observation']['sha256'])
  self.assertEqual(self.requests,[]);self.assertEqual(r.s['phase'],'rates-stop-loss-staging')
 def test_prior_twelve_saved_facts_unchanged(self):
  s=json.loads((DIR/'state.json').read_text());s['details']=s['details'][:12];s['cursor']=12;s['phase']='normal';old=copy.deepcopy(s['details']);d.verify_completed(s,self.m,self.v,require_complete=False);self.assertEqual(s['details'],old)
 def return_runner(self):
  r=self.runner();r.stage(d.nav.digest(r.file),r.s['last_observation']['sha256']);self.policy=True;self.lost=False
  def request(command):
   self.requests.append(command)
   if command['op']=='ping':return {'version':d.nav.VERSION,'safety':'DOM-only','governance_rate_stop_loss_policy':'public-rate-notice-return-v1' if self.policy else 'old'}
   if self.lost:raise RuntimeError('lost-return-reply')
   target=next(n for n in d.g.nodes(self.raw['tree']) if n['selector']==command['locator']['value']);return {'kind':'navigation','version':d.nav.VERSION,'clicked':target}
  r.request=request;return r
 def test_separate_single_return_requires_marker_and_holds_without_advance(self):
  r=self.return_runner();r.return_once();self.assertEqual(r.s['phase'],'rates-stop-loss-return-route-hold');self.assertEqual(r.s['cursor'],0);self.assertEqual(len([c for c in self.requests if c['op']=='click']),1)
  with self.assertRaises(ValueError):r.return_once()
  r.inspect_return();self.assertEqual(len([c for c in self.requests if c['op']=='click']),1)
 def test_unknown_return_only_reads_original_and_never_repeats(self):
  r=self.return_runner();self.lost=True
  with self.assertRaisesRegex(RuntimeError,'lost-return-reply'):r.return_once()
  self.assertEqual(r.s['phase'],'rates-stop-loss-returned-unknown')
  with self.assertRaises(ValueError):r.return_once()
  r.inspect_return();self.assertEqual(r.s['phase'],'rates-stop-loss-return-route-hold');self.assertEqual(len([c for c in self.requests if c['op']=='click']),1)
 def test_old_policy_does_not_issue_navigation(self):
  r=self.return_runner();self.policy=False
  with self.assertRaisesRegex(ValueError,'policy-not-loaded'):r.return_once()
  self.assertFalse(any(c['op']=='click' for c in self.requests))
 def test_utf8_cli_help_has_no_browser_calls(self):
  result=subprocess.run([sys.executable,str(Path(rates.__file__)),'--help'],capture_output=True,text=True,env={**os.environ,'PYTHONUTF8':'0'});self.assertEqual(result.returncode,0,result.stderr);self.assertIn('--expected-state-sha256',result.stdout)
if __name__=='__main__':unittest.main()
